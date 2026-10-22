"""Application tracker, reminders, interviews, notifications, feedback."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    PLANNING = "planning"
    DOCUMENTS_IN_PROGRESS = "documents_in_progress"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    CLOSED = "closed"


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_application_status", "status"),
        Index("ix_application_company", "company"),
        Index("ix_application_date_applied", "date_applied"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    job_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_listings.id", ondelete="SET NULL"), nullable=True
    )
    company: Mapped[str] = mapped_column(String(300), nullable=False)
    job_title: Mapped[str] = mapped_column(String(300), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300))
    application_url: Mapped[str | None] = mapped_column(String(1000))
    source_name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(
        SAEnum(ApplicationStatus, values_callable=lambda e: [e.value for e in e]),
        default=ApplicationStatus.SAVED,
    )
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cover_letter_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    cv_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    recruiter_name: Mapped[str | None] = mapped_column(String(200))
    recruiter_email: Mapped[str | None] = mapped_column(String(320))
    recruiter_notes: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[date | None] = mapped_column(Date)
    date_applied: Mapped[date | None] = mapped_column(Date)
    follow_up_dates: Mapped[list | None] = mapped_column(JSON, default=list)
    interview_dates: Mapped[list | None] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(String(200))
    user_feedback: Mapped[str | None] = mapped_column(Text)

    events = relationship(
        "ApplicationEvent", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationEvent.occurred_at"
    )
    reminders = relationship("Reminder", back_populates="application", cascade="all, delete-orphan")


class ApplicationEvent(Base, TimestampMixin):
    __tablename__ = "application_events"
    __table_args__ = (Index("ix_app_event_application", "application_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(60))  # status_change/note/interview/followup
    from_status: Mapped[str | None] = mapped_column(String(60))
    to_status: Mapped[str | None] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="events")


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"
    __table_args__ = (Index("ix_reminder_due", "due_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(40))  # deadline/followup/interview/assessment/response/custom
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timezone: Mapped[str | None] = mapped_column(String(64))
    recurrence: Mapped[str | None] = mapped_column(String(40))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    application = relationship("Application", back_populates="reminders")


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"
    __table_args__ = (Index("ix_interview_session_job", "job_listing_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True
    )
    job_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_listings.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300))
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[dict | None] = mapped_column(JSON, default=dict)

    questions = relationship(
        "InterviewQuestion", back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.order_index"
    )


class InterviewQuestion(Base, TimestampMixin):
    __tablename__ = "interview_questions"
    __table_args__ = (Index("ix_interview_question_session", "session_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    follow_ups: Mapped[list | None] = mapped_column(JSON, default=list)

    session = relationship("InterviewSession", back_populates="questions")
    answers = relationship("InterviewAnswer", back_populates="question", cascade="all, delete-orphan")


class InterviewAnswer(Base, TimestampMixin):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSON, default=dict)
    feedback: Mapped[str | None] = mapped_column(Text)
    suggested_improvements: Mapped[list | None] = mapped_column(JSON, default=list)
    evidence_used: Mapped[list | None] = mapped_column(JSON, default=list)

    question = relationship("InterviewQuestion", back_populates="answers")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notification_read", "is_read"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str | None] = mapped_column(String(40))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    related_type: Mapped[str | None] = mapped_column(String(40))
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class UserFeedback(Base, TimestampMixin):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(60))  # correction/rating/suggestion
    content: Mapped[dict | None] = mapped_column(JSON, default=dict)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
