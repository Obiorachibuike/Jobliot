"""Health and session-info endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.security import get_or_create_api_token

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    settings = get_settings()
    healthy = True
    try:
        get_engine().connect().close()
    except Exception:
        healthy = False
    return {
        "status": "ok" if healthy else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "auth_required": settings.api_require_auth,
        "database": settings.resolved_database_url.split("://")[0],
    }


@router.get("/token")
def issue_token_info() -> dict:
    """Return whether auth is required (token itself is not exposed via API)."""
    settings = get_settings()
    return {
        "auth_required": settings.api_require_auth,
        "token_exists": bool(get_or_create_api_token()),
    }
