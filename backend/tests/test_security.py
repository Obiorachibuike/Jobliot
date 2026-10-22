"""Security tests: SSRF protection, URL validation, input guards."""

from __future__ import annotations

import pytest

from app.core.security import (
    UnsafeUrlError,
    sanitize_error,
    validate_outbound_url,
)


def test_rejects_localhost():
    ok, reason = validate_outbound_url("http://localhost:8000/admin")
    assert ok is False
    assert "localhost" in reason.lower() or "private" in reason.lower()


def test_rejects_loopback_ip():
    ok, _ = validate_outbound_url("http://127.0.0.1:8080/")
    assert ok is False


def test_rejects_private_ip():
    ok, _ = validate_outbound_url("http://192.168.1.1/router")
    assert ok is False


def test_rejects_metadata_endpoint():
    ok, _ = validate_outbound_url("http://169.254.169.254/latest/meta-data")
    assert ok is False


def test_rejects_non_http_scheme():
    ok, _ = validate_outbound_url("file:///etc/passwd")
    assert ok is False


def test_rejects_nonstandard_port():
    ok, reason = validate_outbound_url("http://example.com:8080/")
    assert ok is False


def test_allows_public_https():
    ok, _ = validate_outbound_url("https://example.com/jobs/123")
    assert ok is True


def test_rejects_link_local_ip():
    ok, _ = validate_outbound_url("http://169.254.1.1/")
    assert ok is False


def test_rejects_oob_reserved_ip():
    ok, _ = validate_outbound_url("http://10.0.0.5/internal")
    assert ok is False


def test_safe_fetch_blocks_local_target():
    from app.core.security import safe_fetch

    with pytest.raises(UnsafeUrlError):
        safe_fetch("http://127.0.0.1:9999/secret")


def test_sanitize_error_hides_secrets():
    message = sanitize_error(Exception("failed with api_key=SUPERSECRET"))
    assert "SUPERSECRET" not in message
    assert "api_key" not in message.lower()


def test_sanitize_error_truncates():
    long_message = "x" * 1000
    assert len(sanitize_error(Exception(long_message))) <= 400
