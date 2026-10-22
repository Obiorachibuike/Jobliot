"""Schemas for applications, reminders, interviews, insights, tasks, privacy."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- applications
class ApplicationCreate(BaseModel):
    job_listing_id: int | None = None
    company: str
    job_title: str
    location: str | None = None
    application_url: str | None = None
    source_name: str | None = None
    status: str | None = "saved"
    deadline: date | None = None
    match_score: float | None = None
    cover_letter_document_id: int | None = None
    cv_document_id: int | None = None
    notes: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: str | None = None
    outcome: str | None = None


class ApplicationEventOut(BaseModel):
    id: int
    application_id: int
    event_type: str
    from_status: str | None = None
    to_status: str | None = None
    notes: str | None = None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class ApplicationOut(BaseModel):
    id: int
    job_listing_id: int | None = None
    company: str
    job_title: str
    location: str | None = None
    application_url: str | None = None
    source_name: str | None = None
    status: str
    match_score: float | None = None
    deadline: date | None = None
    date_applied: date | None = None
    follow_up_dates: list | None = None
    interview_dates: list | None = None
    notes: str | None = None
    outcome: str | None = None
    user_feedback: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    created_at: datetime
    updated_at: datetime
    events: list[ApplicationEventOut] = []

    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    application_url: str | None = None
    source_name: str | None = None
    deadline: date | None = None
    date_applied: date | None = None
    interview_dates: list | None = None
    follow_up_dates: list | None = None
    notes: str | None = None
    outcome: str | None = None
    user_feedback: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    recruiter_notes: str | None = None
    match_score: float | None = None


# --------------------------------------------------------------------------- reminders
class ReminderCreate(BaseModel):
    application_id: int | None = None
    kind: str = "custom"
    title: str
    description: str | None = None
    due_at: datetime
    timezone: str | None = None
    recurrence: str | None = None


class ReminderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
    is_done: bool | None = None
    recurrence: str | None = None


class ReminderOut(BaseModel):
    id: int
    application_id: int | None = None
    kind: str
    title: str
    description: str | None = None
    due_at: datetime
    timezone: str | None = None
    recurrence: str | None = None
    is_done: bool
    reminded_at: datetime | None = None

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- interviews
class InterviewSessionCreate(BaseModel):
    job_listing_id: int | None = None
    application_id: int | None = None
    title: str | None = None


class InterviewAnswerIn(BaseModel):
    answer_text: str
    duration_seconds: int | None = None


class InterviewAnswerOut(BaseModel):
    id: int
    question_id: int
    answer_text: str
    duration_seconds: int | None = None
    scores: dict | None = None
    feedback: str | None = None
    suggested_improvements: list | None = None
    evidence_used: list | None = None

    model_config = {"from_attributes": True}


class InterviewQuestionOut(BaseModel):
    id: int
    category: str
    question: str
    order_index: int
    follow_ups: list | None = None
    answer: InterviewAnswerOut | None = None

    model_config = {"from_attributes": True}


class InterviewSessionOut(BaseModel):
    id: int
    title: str
    job_listing_id: int | None = None
    application_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    overall_score: float | None = None
    summary: str | None = None
    feedback: dict | None = None
    questions: list[InterviewQuestionOut] = []

    model_config = {"from_attributes": True}


class InterviewEvaluation(BaseModel):
    scores: dict
    feedback: str
    suggested_improvements: list[str] = []
    evidence_used: list[str] = []


# --------------------------------------------------------------------------- insights
class InsightOut(BaseModel):
    id: str
    title: str
    description: str
    kind: str  # strength/gap/trend/source/review
    metric: str | None = None
    evidence: dict | None = None
    how_calculated: str
    dismissed: bool = False


class InsightsOut(BaseModel):
    generated_at: datetime
    insights: list[InsightOut] = []
    stats: dict = {}


# --------------------------------------------------------------------------- tasks
class TaskOut(BaseModel):
    id: int
    task_type: str
    name: str
    status: str
    progress: int | None = None
    progress_label: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_details: str | None = None
    result_summary: dict | None = None
    cancellable: bool
    cancel_requested: bool
    attempts: int

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- privacy
class DataExportOut(BaseModel):
    filename: str
    content_b64: str
    size_bytes: int


class BackupInfo(BaseModel):
    path: str
    size_bytes: int
    created_at: datetime


class DeleteScope(BaseModel):
    scope: str = "documents"
    document_ids: list[int] = []
    job_ids: list[int] = []
    application_ids: list[int] = []


class DeleteScopeRequest(BaseModel):
    scope: str = Field(pattern="^(everything|documents|jobs|applications)$")
    document_ids: list[int] = []
    job_ids: list[int] = []
    application_ids: list[int] = []
    confirm: bool = False
