"""Privacy: data export, deletion, backup, restore."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine


def export_all_data(session: Session) -> dict:
    """Export every user-owned table as JSON (no secrets included)."""
    from app.models.ai import AIProviderConfiguration, AIUsageRecord, AppSetting
    from app.models.applications import (
        Application,
        ApplicationEvent,
        InterviewAnswer,
        InterviewQuestion,
        InterviewSession,
        Notification,
        Reminder,
    )
    from app.models.documents import CVVersion, Document, DocumentVersion, MasterCV
    from app.models.jobs import JobListing, JobMatch, JobSearch, JobSource
    from app.models.profile import (
        Achievement,
        CareerPreference,
        Certification,
        Education,
        Project,
        Skill,
        UserProfile,
        WorkExperience,
        WritingStyleProfile,
    )

    def dump(model, order_by="id"):
        rows = session.query(model).order_by(order_by).all()
        return [_serialize(row) for row in rows]

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "product": "CareerPilot AI",
        "version": get_settings().app_version,
        "profile": dump(UserProfile),
        "experience": dump(WorkExperience),
        "education": dump(Education),
        "skills": dump(Skill),
        "projects": dump(Project),
        "certifications": dump(Certification),
        "achievements": dump(Achievement),
        "preferences": dump(CareerPreference),
        "writing_style": dump(WritingStyleProfile),
        "master_cv": dump(MasterCV),
        "cv_versions": dump(CVVersion),
        "documents": dump(Document),
        "document_versions": dump(DocumentVersion),
        "job_sources": dump(JobSource),
        "job_listings": dump(JobListing),
        "job_matches": dump(JobMatch),
        "job_searches": dump(JobSearch),
        "applications": dump(Application),
        "application_events": dump(ApplicationEvent),
        "interview_sessions": dump(InterviewSession),
        "interview_questions": dump(InterviewQuestion),
        "interview_answers": dump(InterviewAnswer),
        "reminders": dump(Reminder),
        "notifications": dump(Notification),
        "ai_usage": dump(AIUsageRecord),
        "settings": dump(AppSetting),
    }
    # Deliberately excluded: provider API keys (secret store),
    # the local API token.
    return data


def _serialize(row) -> dict:
    data = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, (datetime,)):
            value = value.isoformat()
        data[column.name] = value
    return data


def delete_everything(session: Session) -> None:
    """Delete all user data (every table except settings schema)."""
    from app.models.ai import AIProviderConfiguration, AIUsageRecord, AppSetting
    from app.models.applications import (
        Application,
        ApplicationEvent,
        InterviewAnswer,
        InterviewQuestion,
        InterviewSession,
        Notification,
        Reminder,
    )
    from app.models.documents import CVVersion, Document, DocumentVersion, MasterCV
    from app.models.jobs import JobListing, JobMatch, JobSearch, JobSource
    from app.models.profile import (
        Achievement,
        CareerPreference,
        Certification,
        Education,
        Project,
        Skill,
        UserProfile,
        WorkExperience,
        WritingStyleProfile,
    )

    tables = [
        InterviewAnswer, InterviewQuestion, InterviewSession,
        ApplicationEvent, Reminder, Application, Notification,
        DocumentVersion, Document, CVVersion, MasterCV,
        JobMatch, JobListing, JobSearch, JobSource,
        Achievement, Certification, Project, Skill, Education,
        WorkExperience, CareerPreference, WritingStyleProfile,
        UserProfile, AIUsageRecord, AIProviderConfiguration,
    ]
    for model in tables:
        session.query(model).delete()
    session.commit()


def delete_documents(session: Session, document_ids: list[int]) -> int:
    from app.models.documents import Document

    count = 0
    for document_id in document_ids:
        document = session.get(Document, document_id)
        if document is not None:
            session.delete(document)
            count += 1
    session.commit()
    return count


def delete_jobs(session: Session, listing_ids: list[int]) -> int:
    from app.models.jobs import JobListing

    count = 0
    for listing_id in listing_ids:
        listing = session.get(JobListing, listing_id)
        if listing is not None:
            session.delete(listing)
            count += 1
    session.commit()
    return count


def delete_applications(session: Session, application_ids: list[int]) -> int:
    from app.models.applications import Application

    count = 0
    for application_id in application_ids:
        application = session.get(Application, application_id)
        if application is not None:
            session.delete(application)
            count += 1
    session.commit()
    return count


def backup_database(target_path: Path | None = None) -> Path:
    settings = get_settings()
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    if target_path is None:
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        target_path = settings.backup_dir / f"careerpilot-{stamp}.db"
    source = settings.database_path
    if source.exists():
        shutil.copy2(source, target_path)
    return target_path


def restore_database(backup_path: Path) -> None:
    """Replace the current database with a backup copy.

    The caller must ensure the backup file is a valid SQLite
    database; integrity is verified before replacing.
    """
    settings = get_settings()
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    # Verify integrity of the backup first.
    test = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
    try:
        result = test.execute("PRAGMA integrity_check").fetchone()
        if result and result[0] != "ok":
            raise ValueError("Backup file failed integrity check.")
    finally:
        test.close()
    shutil.copy2(backup_path, settings.database_path)


def database_integrity_check() -> dict:
    settings = get_settings()
    if not settings.database_path.exists():
        return {"ok": False, "error": "Database file does not exist"}
    try:
        connection = sqlite3.connect(str(settings.database_path))
        result = connection.execute("PRAGMA integrity_check").fetchone()
        connection.close()
        return {"ok": result and result[0] == "ok", "detail": result[0] if result else None}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
