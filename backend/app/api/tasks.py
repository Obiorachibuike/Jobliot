"""Background tasks API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.ai import BackgroundTask
from app.services.tasks.manager import task_manager

router = APIRouter(prefix="/api/v1/tasks", dependencies=[TokenDep])


@router.get("")
def list_tasks(limit: int = 50, session: SessionDep = None):
    return (
        session.query(BackgroundTask)
        .order_by(BackgroundTask.id.desc())
        .limit(min(limit, 200))
        .all()
    )


@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, session: SessionDep):
    ok = task_manager.request_cancel(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found or already finished")
    return {"ok": True}


@router.get("/stats")
def task_stats(session: SessionDep):
    from sqlalchemy import func

    counts = dict(
        session.query(BackgroundTask.status, func.count(BackgroundTask.id))
        .group_by(BackgroundTask.status)
        .all()
    )
    return counts
