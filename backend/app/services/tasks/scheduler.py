"""Lightweight local scheduler (APScheduler).

Scheduled searches and reminder checks run *while the
application is running*.  A closed desktop application
cannot perform background work - this is stated plainly in
the UI and documentation rather than implied otherwise.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.models.applications import Notification
from app.models.jobs import JobSearch
from app.services.jobs_service import discover_from_sources
from app.services.tasks.manager import task_manager

logger = logging.getLogger("careerpilot.scheduler")

scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global scheduler
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled by configuration.")
        return
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(check_reminders, "interval", seconds=settings.reminder_poll_seconds, id="reminders")
    scheduler.add_job(sync_search_schedules, "interval", minutes=5, id="search-schedule-sync")
    scheduler.start()
    logger.info("Local scheduler started.")


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None


def sync_search_schedules() -> None:
    """(Re)register scheduled job searches."""
    if scheduler is None:
        return
    session = get_session_factory()()
    try:
        searches = session.query(JobSearch).filter(JobSearch.is_active.is_(True)).all()
        registered_ids = {job.id for job in scheduler.get_jobs()}
        for search in searches:
            job_id = f"search-{search.id}"
            if job_id in registered_ids or not search.schedule_cron:
                continue
            try:
                scheduler.add_job(
                    run_scheduled_search,
                    "cron",
                    args=[search.id],
                    id=job_id,
                    **_cron_kwargs(search.schedule_cron),
                )
            except Exception as exc:
                logger.warning("Could not schedule search %s: %s", search.id, exc)
    finally:
        session.close()


def _cron_kwargs(expression: str) -> dict:
    parts = expression.strip().split()
    if len(parts) == 5:
        minute, hour, day, month, weekday = parts
        return {
            "minute": _wildcard_or_int(minute),
            "hour": _wildcard_or_int(hour),
            "day": _wildcard_or_int(day),
            "month": _wildcard_or_int(month),
            "day_of_week": weekday,
        }
    return {"minute": "*/30"}


def _wildcard_or_int(value: str):
    return int(value) if value.isdigit() else value


def run_scheduled_search(search_id: int) -> None:
    session = get_session_factory()()
    try:
        search = session.get(JobSearch, search_id)
        if search is None or not search.is_active:
            return
        task = task_manager.create_task(
            "scheduled_search",
            f"Scheduled search: {search.name}",
            payload={"search_id": search_id},
        )
        filters = search.filters or {}
        from app.services.jobs.base import SearchQuery

        query = SearchQuery(
            title=search.query or None,
            limit=int(filters.get("limit", 25) or 25),
        )
        result = discover_from_sources(session, query, search.source_ids or None)
        search.last_run = datetime.utcnow()
        session.commit()
        task_manager.update_progress(task.id, 100, "Completed")
    except Exception as exc:
        logger.exception("Scheduled search failed")
    finally:
        session.close()


def check_reminders() -> None:
    """Create notifications for due reminders (runs only while app is open)."""
    session = get_session_factory()()
    try:
        now = datetime.utcnow()
        window = now + timedelta(hours=24)
        from app.models.applications import Reminder

        due = (
            session.query(Reminder)
            .filter(Reminder.is_done.is_(False), Reminder.due_at <= window)
            .all()
        )
        for reminder in due:
            if reminder.reminded_at and reminder.reminded_at > now - timedelta(hours=1):
                continue
            exists = (
                session.query(Notification)
                .filter(
                    Notification.related_type == "reminder",
                    Notification.related_id == reminder.id,
                )
                .first()
            )
            if exists:
                continue
            session.add(
                Notification(
                    title=f"Reminder: {reminder.title}",
                    body=reminder.description or "",
                    kind="reminder",
                    related_type="reminder",
                    related_id=reminder.id,
                )
            )
            reminder.reminded_at = now
        session.commit()
    except Exception:
        logger.exception("Reminder check failed")
        session.rollback()
    finally:
        session.close()
