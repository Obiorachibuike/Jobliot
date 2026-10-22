"""General settings and notifications API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.applications import Notification
from app.schemas.ai import SettingsOut, SettingsUpdate
from app.services.settings_service import get_settings, update_settings

router = APIRouter(prefix="/api/v1", dependencies=[TokenDep])


@router.get("/settings", response_model=SettingsOut)
def read_settings(session: SessionDep):
    return get_settings(session)


@router.patch("/settings", response_model=SettingsOut)
def write_settings(payload: SettingsUpdate, session: SessionDep):
    return update_settings(session, payload.model_dump(exclude_unset=True))


@router.get("/notifications")
def list_notifications(session: SessionDep, limit: int = 50):
    return (
        session.query(Notification)
        .order_by(Notification.id.desc())
        .limit(min(limit, 200))
        .all()
    )


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, session: SessionDep):
    notification = session.get(Notification, notification_id)
    if notification is None:
        return {"ok": False, "detail": "Notification not found"}
    notification.is_read = True
    session.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def mark_all_read(session: SessionDep):
    session.query(Notification).update({Notification.is_read: True})
    session.commit()
    return {"ok": True}
