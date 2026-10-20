import hashlib, ipaddress, os, secrets, socket
from pathlib import Path
from urllib.parse import urlparse
from app.db import DATA_DIR
_TOKEN_FILE = DATA_DIR/".api_token"
def get_api_token() -> str:
    env = os.environ.get("CAREERPILOT_API_TOKEN")
    if env: return env
    if _TOKEN_FILE.exists(): return _TOKEN_FILE.read_text().strip()
    t = secrets.token_urlsafe(32); _TOKEN_FILE.write_text(t)
    try: _TOKEN_FILE.chmod(0o600)
    except OSError: pass
    return t
def hash_key(k: str) -> str: return hashlib.sha256(k.encode()).hexdigest()
def get_stored_api_key() -> str:
    try:
        import keyring  # type: ignore
        v = keyring.get_password("careerpilot-ai", "ai_api_key")
        if v: return v
    except Exception: pass
    f = DATA_DIR/".ai_key"
    return f.read_text().strip() if f.exists() else ""
def store_api_key(k: str) -> str:
    """Returns storage backend name. Prefers OS keyring; falls back to 0600 file (documented)."""
    try:
        import keyring  # type: ignore
        keyring.set_password("careerpilot-ai", "ai_api_key", k); return "os-keyring"
    except Exception: pass
    f = DATA_DIR/".ai_key"; f.write_text(k)
    try: f.chmod(0o600)
    except OSError: pass
    return "restricted-file (OS keyring unavailable — file permissions 0600)"
def clear_api_key():
    try:
        import keyring  # type: ignore
        keyring.delete_password("careerpilot-ai", "ai_api_key")
    except Exception: pass
    f = DATA_DIR/".ai_key"
    if f.exists(): f.unlink()
BLOCKED_HOSTS={"localhost","metadata.google.internal"}
def validate_public_url(url: str) -> tuple[bool,str]:
    try: p=urlparse(url)
    except Exception: return False,"Invalid URL"
    if p.scheme not in ("http","https"): return False,"Only http/https URLs are allowed"
    host=(p.hostname or "").lower()
    if not host or host in BLOCKED_HOSTS: return False,"Host is not allowed"
    if p.port not in (None,80,443): return False,"Only ports 80 and 443 are allowed"
    try:
        infos=socket.getaddrinfo(host, p.port or (443 if p.scheme=="https" else 80), proto=socket.IPPROTO_TCP)
    except Exception as e: return False,f"Could not resolve host: {e}"
    for info in infos:
        ip=ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False,"Private, loopback, or metadata addresses are blocked (SSRF protection)"
    return True,"ok"
