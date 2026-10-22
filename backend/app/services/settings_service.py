"""Application settings service (single-row JSON settings)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai import AppSetting
from app.schemas.ai import SettingsOut

DEFAULTS = {
    "theme": "system",
    "review_rounds": 2,
    "match_weights": {},
    "scheduler_enabled": True,
    "max_daily_recommendations": 10,
    "notifications_enabled": True,
    "default_template_id": "ats_friendly",
    "match_category_thresholds": {
        "strong": 75,
        "consider": 55,
        "stretch": 35,
    },
}


def get_settings_row(session: Session) -> AppSetting:
    row = session.query(AppSetting).first()
    if row is None:
        row = AppSetting(settings=dict(DEFAULTS))
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


def get_settings(session: Session) -> dict:
    row = get_settings_row(session)
    merged = dict(DEFAULTS)
    merged.update(row.settings or {})
    return merged


def update_settings(session: Session, updates: dict) -> dict:
    row = get_settings_row(session)
    current = dict(row.settings or {})
    for key, value in updates.items():
        if key in DEFAULTS:
            current[key] = value
    row.settings = current
    session.commit()
    merged = dict(DEFAULTS)
    merged.update(current)
    return merged


def get_match_weights(session: Session) -> dict:
    settings = get_settings(session)
    return settings.get("match_weights") or {}


def get_review_rounds(session: Session) -> int:
    settings = get_settings(session)
    return int(settings.get("review_rounds") or 2)
