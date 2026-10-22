"""Application configuration for the CareerPilot AI backend.

All paths and tunables are configurable through environment variables or a
``.env`` file.  No secrets belong in source control; see ``.env.example``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATA_DIR = Path.home() / ".careerpilot"


class Settings(BaseSettings):
    """Runtime settings loaded from environment / ``.env`` (prefix CAREERPILOT_)."""

    model_config = SettingsConfigDict(env_prefix="CAREERPILOT_", extra="ignore")

    app_name: str = "CareerPilot AI"
    app_version: str = "0.1.0"
    environment: str = "development"

    # --- storage -----------------------------------------------------------
    data_dir: str = str(DEFAULT_DATA_DIR)
    database_url: str = ""  # empty -> sqlite file inside data_dir

    # --- local API security ------------------------------------------------
    # When True every request (except /health) must present the install token.
    # The token is generated on first run and stored with 0600 permissions.
    api_require_auth: bool = True
    api_token: str = ""  # if empty, one is generated and persisted

    # Origins allowed for CORS.  The Electron shell loads the UI via a
    # custom protocol (origin "null" for file:// pages) and the Vite dev
    # server uses http://localhost:5173.
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    host: str = "127.0.0.1"
    port: int = 8787

    # --- request safety ----------------------------------------------------
    request_max_bytes: int = 16 * 1024 * 1024

    # --- outbound fetch safety (job URL import) ----------------------------
    job_fetch_timeout_seconds: float = 15.0
    job_fetch_max_bytes: int = 4 * 1024 * 1024
    job_fetch_max_redirects: int = 4

    # --- AI defaults -------------------------------------------------------
    ai_default_temperature: float = 0.3
    ai_default_max_tokens: int = 2048
    ai_default_timeout_seconds: float = 120.0
    ai_default_retries: int = 2

    # --- multi-agent workflow ----------------------------------------------
    review_rounds_default: int = 2

    # --- background work ---------------------------------------------------
    scheduler_enabled: bool = True
    reminder_poll_seconds: int = 60

    log_level: str = "INFO"

    # ------------------------------------------------------------------ utils
    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).expanduser()

    @property
    def database_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return self.data_path / "careerpilot.db"

    @property
    def backup_dir(self) -> Path:
        return self.data_path / "backups"

    @property
    def documents_dir(self) -> Path:
        return self.data_path / "documents"

    @property
    def uploads_dir(self) -> Path:
        return self.data_path / "uploads"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.database_path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Primarily useful for tests that reconfigure the environment."""
    get_settings.cache_clear()
