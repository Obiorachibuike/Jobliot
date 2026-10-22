"""Security utilities: local API token, SSRF-safe fetching, input guards.

The backend binds to loopback by default.  Because binding to localhost alone
does not protect against requests from untrusted web pages (DNS rebinding,
malicious browser tabs), every mutating or data-returning endpoint also
requires a per-installation bearer token that is never exposed to the web.
"""

from __future__ import annotations

import hmac
import ipaddress
import logging
import socket
import secrets
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings

logger = logging.getLogger("careerpilot.security")

# Cloud metadata endpoints (AWS/GCP/OpenStack) - always blocked.
_METADATA_HOSTS = {"169.254.169.254", "fd00:ec2::254", "metadata.google.internal"}


class UnsafeUrlError(ValueError):
    """Raised when a URL fails SSRF validation."""


# ---------------------------------------------------------------------------
# per-installation API token
# ---------------------------------------------------------------------------

def _token_path() -> Path:
    settings = get_settings()
    settings.data_path.mkdir(parents=True, exist_ok=True)
    return settings.data_path / "api_token"


def get_or_create_api_token() -> str:
    """Return the install token, generating and persisting it on first use."""
    settings = get_settings()
    if settings.api_token:
        return settings.api_token
    path = _token_path()
    if path.exists():
        token = path.read_text().strip()
        if token:
            return token
    token = secrets.token_urlsafe(32)
    try:
        path.write_text(token)
        Path(path).chmod(0o600)
    except OSError as exc:  # pragma: no cover - platform specific
        logger.warning("Could not persist API token to %s: %s", path, exc)
    return token


def verify_api_token(provided: str | None) -> bool:
    expected = get_or_create_api_token()
    if not provided:
        return False
    # Strip optional "Bearer " prefix for convenience.
    if provided.lower().startswith("bearer "):
        provided = provided[7:].strip()
    return hmac.compare_digest(provided, expected)


# ---------------------------------------------------------------------------
# SSRF protection
# ---------------------------------------------------------------------------

def _ip_is_blocked(ip: str) -> bool:
    try:
        address = ipaddress.ip_address(ip.strip("[]"))
    except ValueError:
        return True  # not a valid IP -> block
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
        or str(address) in _METADATA_HOSTS
    )


def _hostname_is_blocked(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in ("localhost",) or host.endswith(".localhost") or host.endswith(".local"):
        return True
    if host in _METADATA_HOSTS:
        return True
    # Decimal/hex/octal IP obfuscation is handled by ipaddress when parsing
    # fails below - anything weird is rejected at resolution time.
    return False


def validate_outbound_url(
    url: str,
    allowed_schemes: Iterable[str] = ("http", "https"),
    allowed_ports: Iterable[int] = (80, 443),
) -> tuple[bool, str]:
    """Validate a URL for outbound fetching.

    Returns ``(is_safe, reason)``.  Checks scheme, port, hostname, and that the
    resolved address is not a private/loopback/link-local/metadata target.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False, "Malformed URL."

    scheme = (parsed.scheme or "").lower()
    if scheme not in allowed_schemes:
        return False, f"URL scheme '{scheme or '(empty)'}' is not allowed; only http/https."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL has no host."

    if _hostname_is_blocked(hostname):
        return False, "Requests to localhost or internal hostnames are not allowed."

    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 80
    if port not in allowed_ports:
        return False, f"Port {port} is not allowed; only {sorted(allowed_ports)} are permitted."

    if hostname in _METADATA_HOSTS:
        return False, "Cloud metadata endpoints are blocked."

    # Reject IP-literal destinations and verify DNS resolution.
    try:
        literal = ipaddress.ip_address(hostname)
        if _ip_is_blocked(str(literal)):
            return False, "The URL points to a private or reserved IP address."
    except ValueError:
        pass

    try:
        addr_infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False, "The host could not be resolved; the job page may be unavailable."

    for info in addr_infos:
        ip = info[4][0]
        if _ip_is_blocked(ip):
            return False, (
                "The destination resolves to a private, loopback, or reserved "
                "network address, which is not allowed."
            )

    return True, ""


def safe_fetch(
    url: str,
    settings=None,
    extra_headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Fetch a public URL with SSRF protections, redirect re-validation,
    response-size limits, and timeouts.

    Raises :class:`UnsafeUrlError` for policy violations or ``httpx.HTTPError``
    for transport failures.
    """
    settings = settings or get_settings()
    is_safe, reason = validate_outbound_url(url)
    if not is_safe:
        raise UnsafeUrlError(reason)

    headers = {
        "User-Agent": "CareerPilotAI/1.0 (local career assistant; contact: none)",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.1",
        "Accept-Language": "en;q=0.9",
        **(extra_headers or {}),
    }

    timeout = httpx.Timeout(settings.job_fetch_timeout_seconds)
    remaining_redirects = settings.job_fetch_max_redirects
    current = url
    last_response: httpx.Response | None = None

    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        while True:
            is_safe, reason = validate_outbound_url(current)
            if not is_safe:
                raise UnsafeUrlError(f"Redirect target rejected: {reason}")
            try:
                response = client.get(current, headers=headers)
            except httpx.HTTPError as exc:
                raise UnsafeUrlError(f"Could not retrieve the page: {exc}") from exc

            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    raise UnsafeUrlError("Redirect without a Location header.")
                if remaining_redirects <= 0:
                    raise UnsafeUrlError("Too many redirects.")
                remaining_redirects -= 1
                current = httpx.URL(url=current).join(location)
                continue

            if response.status_code != 200:
                raise UnsafeUrlError(f"The server responded with HTTP {response.status_code}.")

            content_length = response.headers.get("content-length")
            if content_length and int(content_length or 0) > settings.job_fetch_max_bytes:
                raise UnsafeUrlError("The page is too large to process safely.")

            # Stream-read with a hard cap so huge responses cannot exhaust memory.
            total = 0
            chunks: list[bytes] = []
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > settings.job_fetch_max_bytes:
                    raise UnsafeUrlError("The page exceeded the safe size limit.")
                chunks.append(chunk)
            response.read = lambda: b"".join(chunks)  # type: ignore[method-assign]
            response._content = b"".join(chunks)  # type: ignore[attr-defined]
            return response


def sanitize_error(exc: Exception) -> str:
    """Return a user-facing error message without internal details."""
    message = str(exc)
    if "api_token" in message.lower() or "secret" in message.lower():
        return "An internal security error occurred."
    return message[:400]
