"""Background task manager.

Tasks are persisted as records so the application can report
real status, recover from interruptions, and cancel work
where safe.  Progress is only reported when it can be
measured; otherwise the task shows an indeterminate state.
"""

from __future__ import annotations

import logging
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.models.ai import BackgroundTask

logger = logging.getLogger("careerpilot.tasks")

MAX_WORKERS = 3


class TaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="careerpilot-task")
        self._futures: dict[int, Any] = {}
        self._cancel_events: dict[int, threading.Event] = {}
        self._lock = threading.Lock()

    def create_task(self, task_type: str, name: str, cancellable: bool = True,
                    payload: dict | None = None) -> BackgroundTask:
        session = get_session_factory()()
        try:
            task = BackgroundTask(
                task_type=task_type,
                name=name,
                status="queued",
                cancellable=cancellable,
                payload=payload or {},
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        finally:
            session.close()

    def submit(self, task_id: int, fn: Callable, *args, **kwargs) -> None:
        def _run():
            session = get_session_factory()()
            try:
                task = session.get(BackgroundTask, task_id)
                if task is None:
                    return
                task.status = "running"
                task.started_at = datetime.utcnow()
                task.attempts = (task.attempts or 0) + 1
                session.commit()

                cancel_event = self._cancel_events.get(task_id, threading.Event())
                result = fn(cancel_event=cancel_event, session=session, *args, **kwargs)

                task = session.get(BackgroundTask, task_id)
                if task.cancel_requested:
                    task.status = "cancelled"
                else:
                    task.status = "completed"
                    task.progress = 100
                    task.result_summary = result if isinstance(result, dict) else {"result": str(result)[:400]}
                task.completed_at = datetime.utcnow()
                session.commit()
            except Exception as exc:
                logger.exception("Task %s failed", task_id)
                try:
                    task = session.get(BackgroundTask, task_id)
                    if task is not None:
                        task.status = "failed"
                        task.error_details = (
                            f"{type(exc).__name__}: {str(exc)[:300]}\n"
                            + traceback.format_exc(limit=3)
                        )
                        task.completed_at = datetime.utcnow()
                        session.commit()
                except Exception:
                    session.rollback()
            finally:
                session.close()
                with self._lock:
                    self._futures.pop(task_id, None)
                    self._cancel_events.pop(task_id, None)

        future = self.executor.submit(_run)
        with self._lock:
            self._futures[task_id] = future

    def request_cancel(self, task_id: int) -> bool:
        session = get_session_factory()()
        try:
            task = session.get(BackgroundTask, task_id)
            if task is None or task.status not in ("queued", "running"):
                return False
            task.cancel_requested = True
            event = self._cancel_events.get(task_id)
            if event is not None:
                event.set()
            session.commit()
            return True
        finally:
            session.close()

    def update_progress(self, task_id: int, progress: int | None, label: str | None) -> None:
        session = get_session_factory()()
        try:
            task = session.get(BackgroundTask, task_id)
            if task is None:
                return
            if progress is not None:
                task.progress = max(0, min(100, progress))
            if label:
                task.progress_label = label[:200]
            session.commit()
        finally:
            session.close()

    def recover_interrupted(self) -> int:
        """Mark tasks left 'running' by an interrupted process."""
        session = get_session_factory()()
        try:
            running = (
                session.query(BackgroundTask)
                .filter(BackgroundTask.status == "running")
                .all()
            )
            for task in running:
                task.status = "failed"
                task.error_details = (
                    "Task was interrupted by an application restart."
                )
                task.completed_at = datetime.utcnow()
            session.commit()
            return len(running)
        finally:
            session.close()

    def list_tasks(self, limit: int = 50) -> list[BackgroundTask]:
        session = get_session_factory()()
        try:
            return (
                session.query(BackgroundTask)
                .order_by(BackgroundTask.id.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()


task_manager = TaskManager()
