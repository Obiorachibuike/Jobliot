"""Application tracker API.

Route ordering matters: static paths (/analytics, /reminders) are
registered BEFORE the dynamic /{application_id} path so they are
never captured as an application id.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.applications import Application, ApplicationEvent, ApplicationStatus, Reminder
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationEventOut,
    ApplicationOut,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    ReminderCreate,
    ReminderOut,
    ReminderUpdate,
)

router = APIRouter(prefix="/api/v1/applications", dependencies=[TokenDep])

VALID_STATUSES = {s.value for s in ApplicationStatus}


# --------------------------------------------------------------------------- list/create
@router.get("", response_model=list[ApplicationOut])
def list_applications(session: SessionDep, status: str | None = None):
    query = session.query(Application).order_by(Application.id.desc())
    if status:
        query = query.filter(Application.status == status)
    return query.all()


@router.post("", response_model=ApplicationOut)
def create_application(payload: ApplicationCreate, session: SessionDep):
    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    from app.services.profile_service import get_or_create_profile

    profile = get_or_create_profile(session)
    data = payload.model_dump()
    data["profile_id"] = profile.id
    application = Application(**data)
    session.add(application)
    session.flush()  # assign application.id before logging the event
    _add_event(session, application, "created", None, payload.status or "saved")
    session.commit()
    session.refresh(application)
    return application


# --------------------------------------------------------------------------- analytics
@router.get("/analytics")
def application_analytics(session: SessionDep):
    applications = session.query(Application).all()
    total = len(applications)
    by_status = Counter(a.status for a in applications)
    by_source = Counter(a.source_name or "unknown" for a in applications if a.source_name)
    by_company = Counter(a.company for a in applications)
    applied = [a for a in applications if a.date_applied]
    interviews = by_status.get("interview", 0)
    offers = by_status.get("offer", 0)
    response_rate = round(100.0 * (interviews + offers) / len(applied), 1) if applied else 0.0

    # Activity by ISO week (last 8 weeks) from record creation.
    now = datetime.utcnow()
    weekly = {}
    for i in range(8):
        iso = (now - timedelta(weeks=7 - i)).date().isocalendar()[:2]
        weekly[f"{iso[0]}-W{iso[1]:02d}"] = 0
    for application in applications:
        if application.created_at:
            iso = application.created_at.date().isocalendar()[:2]
            week_key = f"{iso[0]}-W{iso[1]:02d}"
            if week_key in weekly:
                weekly[week_key] += 1

    return {
        "total_applications": total,
        "by_status": dict(by_status),
        "by_source": dict(by_source),
        "top_companies": by_company.most_common(5),
        "interviews": interviews,
        "offers": offers,
        "response_rate": response_rate,
        "weekly_activity": weekly,
        "data_note": "Computed from stored application records only.",
    }


# --------------------------------------------------------------------------- reminders
@router.get("/reminders", response_model=list[ReminderOut])
def list_reminders(session: SessionDep, include_done: bool = False):
    query = session.query(Reminder).order_by(Reminder.due_at.asc())
    if not include_done:
        query = query.filter(Reminder.is_done.is_(False))
    return query.limit(100).all()


@router.post("/reminders", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, session: SessionDep):
    from app.services.profile_service import get_or_create_profile

    profile = get_or_create_profile(session)
    data = payload.model_dump()
    data["profile_id"] = profile.id
    reminder = Reminder(**data)
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder


@router.patch("/reminders/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, payload: ReminderUpdate, session: SessionDep):
    reminder = session.get(Reminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(reminder, key, value)
    session.commit()
    session.refresh(reminder)
    return reminder


@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, session: SessionDep):
    reminder = session.get(Reminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    session.delete(reminder)
    session.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- per-application CRUD
@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, session: SessionDep):
    application = _get_or_404(session, application_id)
    return application


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(application_id: int, payload: ApplicationUpdate, session: SessionDep):
    application = _get_or_404(session, application_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(application, key, value)
    session.commit()
    session.refresh(application)
    return application


@router.delete("/{application_id}")
def delete_application(application_id: int, session: SessionDep):
    application = _get_or_404(session, application_id)
    session.delete(application)
    session.commit()
    return {"ok": True}


@router.post("/{application_id}/status", response_model=ApplicationOut)
def set_status(application_id: int, payload: ApplicationStatusUpdate, session: SessionDep):
    application = _get_or_404(session, application_id)
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    old_status = application.status
    application.status = payload.status
    if payload.outcome is not None:
        application.outcome = payload.outcome
    _add_event(session, application, "status_change", old_status, payload.status, payload.notes)
    session.commit()
    session.refresh(application)
    return application


@router.get("/{application_id}/events", response_model=list[ApplicationEventOut])
def application_events(application_id: int, session: SessionDep):
    return (
        session.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.occurred_at.desc())
        .all()
    )


@router.post("/{application_id}/notes")
def add_note(application_id: int, notes: str, session: SessionDep):
    application = _get_or_404(session, application_id)
    _add_event(session, application, "note", None, None, notes)
    session.commit()
    return {"ok": True}


def _add_event(session: Session, application: Application, event_type: str,
               from_status: str | None, to_status: str | None, notes: str | None = None) -> None:
    session.add(
        ApplicationEvent(
            application_id=application.id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
        )
    )


def _get_or_404(session: Session, application_id: int) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application
