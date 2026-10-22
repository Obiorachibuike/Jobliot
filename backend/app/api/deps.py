"""FastAPI dependencies: auth, sessions, error handling."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_token
from app.core.config import get_settings


def require_api_token(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    if not settings.api_require_auth:
        return
    if request.url.path.startswith("/api/v1/health"):
        return
    # Allow OpenAPI docs in development only.
    if settings.environment == "development" and request.url.path.startswith("/openapi.json"):
        return
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Missing or invalid API token.")


def get_db_session() -> Session:
    return get_db()


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Depends(require_api_token)
