"""Secret storage for AI provider API keys.

Two tiers:
1. OS keyring (keyring package) when available - preferred.
2. Encrypted file store (Fernet) with a machine-local key file
   restricted to 0600 permissions.

Keys are never written to the database, logs, or the frontend.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger("careerpilot.secrets")

_KEY_FILE = "secret.key"
_SECRETS_FILE = "secrets.json"

_keyring = None
_keyring_error: str | None = None
try:  # pragma: no cover - optional dependency
    import keyring as _keyring_module

    _keyring = _keyring_module
except Exception as exc:  # pragma: no cover
    _keyring_error = str(exc)


def _key_path() -> Path:
    path = get_settings().data_path / _KEY_FILE
    return path


def _secrets_path() -> Path:
    return get_settings().data_path / _SECRETS_FILE


def _get_cipher():
    from cryptography.fernet import Fernet

    key_path = _key_path()
    if not key_path.exists():
        key = Fernet.generate_key()
        key_path.write_bytes(key)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass
    else:
        key = key_path.read_bytes().strip()
    return Fernet(key)


def _file_store() -> dict:
    path = _secrets_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_file_store(data: dict) -> None:
    path = _secrets_path()
    path.write_text(json.dumps(data))
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def store_secret(key: str, value: str) -> None:
    if _keyring is not None:
        try:
            _keyring.set_password("careerpilot", key, value)
            return
        except Exception as exc:  # pragma: no cover
            logger.warning("Keyring unavailable (%s); using encrypted file store.", exc)
    store = _file_store()
    cipher = _get_cipher()
    store[key] = cipher.encrypt(value.encode()).decode()
    _write_file_store(store)


def retrieve_secret(key: str) -> str | None:
    if _keyring is not None:
        try:
            value = _keyring.get_password("careerpilot", key)
            if value is not None:
                return value
        except Exception:  # pragma: no cover
            pass
    store = _file_store()
    payload = store.get(key)
    if not payload:
        return None
    cipher = _get_cipher()
    try:
        return cipher.decrypt(payload.encode()).decode()
    except Exception:
        return None


def delete_secret(key: str) -> None:
    if _keyring is not None:
        try:
            _keyring.delete_password("careerpilot", key)
        except Exception:  # pragma: no cover
            pass
    store = _file_store()
    store.pop(key, None)
    _write_file_store(store)


def secret_backend() -> str:
    if _keyring is not None:
        try:
            _keyring.get_password("careerpilot", "probe")
            return "os-keyring"
        except Exception:
            pass
    return "encrypted-file"
