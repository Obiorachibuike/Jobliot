"""Schemas for documents, the application studio, and exports."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.profile import VerificationStatusOut


class DocumentBlock(BaseModel):
    type: str  # paragraph|bullets|entry|lines|date_range|heading
    text: str | None = None
    title: str | None = None
    organization: str | None = None
    date_range: str | None = None
    items: list[str] | None = None
    lines: list[str] | None = None
    meta: str | None = None


class DocumentSection(BaseModel):
    id: str
    heading: str
    blocks: list[DocumentBlock] = []


class StructuredDocument(BaseModel):
    title: str
    subtitle: str | None = None
    contact_line: str | None = None
    template_id: str = "ats_friendly"
    sections: list[DocumentSection] = []


class DocumentTemplateOut(BaseModel):
    id: str
    name: str
    description: str
    layout: str
    best_for: list[str] = []
    ats_safe: bool = True


class MasterCVOut(BaseModel):
    id: int
    title: str
    template_id: str
    content: dict
    version: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class CVVersionOut(BaseModel):
    id: int
    version_number: int
    content: dict
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    profile_id: int
    job_listing_id: int | None = None
    application_id: int | None = None
    kind: str
    title: str
    template_id: str
    status: str
    content: dict | None = None
    strategy: dict | None = None
    match_data: dict | None = None
    approved_by_user: bool
    current_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentVersionOut(BaseModel):
    id: int
    version_number: int
    content: dict
    status: str | None = None
    change_summary: str | None = None
    agent_stage: str | None = None
    findings: list = []
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    job_listing_id: int | None = None
    kind: str = "cv"
    template_id: str = "ats_friendly"
    title: str | None = None
    cover_letter_length: str | None = "standard"


class DocumentUpdate(BaseModel):
    title: str | None = None
    template_id: str | None = None
    content: dict | None = None


class ReviewFinding(BaseModel):
    id: str
    severity: str  # critical/major/minor/suggestion
    category: str
    location: str | None = None
    message: str
    evidence: str | None = None
    recommendation: str | None = None
    requires_user_confirmation: bool = False
    resolved: bool = False


class ReviewResultOut(BaseModel):
    findings: list[ReviewFinding] = []
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    suggestion_count: int = 0
    overall_assessment: str | None = None
    readiness: str  # not_ready/ready/needs_confirmation


class StrategyOut(BaseModel):
    positioning: str | None = None
    selected_experience: list[dict] = []
    selected_projects: list[dict] = []
    selected_skills: list[str] = []
    key_messages: list[str] = []
    gaps: list[str] = []
    gap_mitigations: list[str] = []
    keyword_targets: list[str] = []
    evidence_refs: list[dict] = []


class RevisionResult(BaseModel):
    content: dict
    changes: list[dict] = []
    findings_addressed: list[str] = []
    findings_unresolved: list[dict] = []
    status: str
    requires_user_confirmation: bool = False


class ExportRequest(BaseModel):
    format: str = Field(pattern="^(pdf|docx|txt|tex)$")


class ExportResult(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int
    content_b64: str
    validator: dict | None = None


class ReviewRoundsConfig(BaseModel):
    rounds: int = Field(default=2, ge=1, le=5)


class AgentStage(str, Enum):
    STRATEGY = "strategy"
    DRAFT = "draft"
    REVIEW = "review"
    REVISION = "revision"
    USER = "user"
