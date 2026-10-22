"""Shared API response schemas and error model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class OkResponse(BaseModel):
    ok: bool = True
    detail: str | None = None


class PaginationParams(BaseModel):
    limit: int = 50
    offset: int = 0


def camel(obj: dict[str, Any]) -> dict[str, Any]:
    """Utility kept for clarity in routers that post-process payloads."""
    return obj
