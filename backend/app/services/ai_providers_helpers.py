"""Helper to fetch the default AI provider configuration."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai import AIProviderConfiguration


def get_default_adapter_config(session: Session) -> AIProviderConfiguration | None:
    default = (
        session.query(AIProviderConfiguration)
        .filter(AIProviderConfiguration.is_default.is_(True))
        .first()
    )
    if default is not None and default.enabled:
        return default
    return (
        session.query(AIProviderConfiguration)
        .filter(AIProviderConfiguration.enabled.is_(True))
        .order_by(AIProviderConfiguration.id.asc())
        .first()
    )
