"""Document models: master CV, tailored documents, versions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DocumentKind(str, Enum):
    CV = "cv"
    COVER_LETTER = "cover_letter"
    OTHER = "other"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    NEEDS_USER_CONFIRMATION = "needs_user_confirmation"
    REVISION_REQUIRED = "revision_required"
    READY_FOR_APPROVAL = "ready_for_approval"
    APPROVED = "approved"
    EXPORTED = "exported"


class MasterCV(Base, TimestampMixin):
    """The user's canonical CV, kept separate from tailored versions."""

    __tablename__ = "master_cvs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(String(240), default="Master CV")
    template_id: Mapped[str] = mapped_column(String(80), default="ats_friendly")
    content: Mapped[dict] = mapped_column(JSON, default=dict)  # structured document
    auto_generate_from_profile: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    profile = relationship("UserProfile", back_populates="master_cv")
    versions = relationship(
        "CVVersion", back_populates="master_cv", cascade="all, delete-orphan", order_by="CVVersion.version_number"
    )


class CVVersion(Base, TimestampMixin):
    __tablename__ = "cv_versions"
    __table_args__ = (Index("ix_cv_version_master", "master_cv_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_cv_id: Mapped[int] = mapped_column(
        ForeignKey("master_cvs.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str | None] = mapped_column(String(300))

    master_cv = relationship("MasterCV", back_populates="versions")


class Document(Base, TimestampMixin):
    """A tailored application document (CV or cover letter)."""

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_document_profile", "profile_id"),
        Index("ix_document_job", "job_listing_id"),
        Index("ix_document_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    job_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_listings.id", ondelete="SET NULL"), nullable=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(SAEnum(DocumentKind, values_callable=lambda e: [e.value for e in e]))
    title: Mapped[str] = mapped_column(String(300))
    template_id: Mapped[str] = mapped_column(String(80), default="ats_friendly")
    status: Mapped[str] = mapped_column(
        SAEnum(DocumentStatus, values_callable=lambda e: [e.value for e in e]),
        default=DocumentStatus.DRAFT,
    )
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    strategy: Mapped[dict | None] = mapped_column(JSON)  # application strategy snapshot
    match_data: Mapped[dict | None] = mapped_column(JSON)  # match report snapshot
    meta: Mapped[dict | None] = mapped_column(JSON, default=dict)
    approved_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)

    versions = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version_number"
    )


class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"
    __table_args__ = (Index("ix_doc_version_document", "document_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str | None] = mapped_column(String(40))
    change_summary: Mapped[str | None] = mapped_column(String(400))
    agent_stage: Mapped[str | None] = mapped_column(String(40))  # strategy/draft/review/revision/user
    findings: Mapped[list | None] = mapped_column(JSON, default=list)

    document = relationship("Document", back_populates="versions")
