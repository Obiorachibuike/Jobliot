"""Job discovery models: sources, listings, matches, saved searches."""

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


class JobSourceType(str, Enum):
    MANUAL = "manual"
    URL = "url_import"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"
    NOT_RECENTLY_VERIFIED = "not_recently_verified"


class JobSource(Base, TimestampMixin):
    __tablename__ = "job_sources"
    __table_args__ = (Index("ix_job_source_type", "source_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(
        SAEnum(JobSourceType, values_callable=lambda e: [e.value for e in e])
    )
    config: Mapped[dict | None] = mapped_column(JSON, default=dict)  # e.g. company token
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health_status: Mapped[str | None] = mapped_column(String(30), default="unknown")
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=False)


class JobListing(Base, TimestampMixin):
    __tablename__ = "job_listings"
    __table_args__ = (
        Index("ix_job_listing_dedup", "dedup_hash"),
        Index("ix_job_listing_company", "company"),
        Index("ix_job_listing_title", "title"),
        Index("ix_job_listing_location", "location"),
        Index("ix_job_listing_discovered", "date_discovered"),
        Index("ix_job_listing_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(300))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(300), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300))
    workplace_type: Mapped[str | None] = mapped_column(String(40))  # remote/hybrid/onsite
    employment_type: Mapped[str | None] = mapped_column(String(60))
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_qualifications: Mapped[list | None] = mapped_column(JSON, default=list)
    publication_date: Mapped[date | None] = mapped_column(Date)
    closing_date: Mapped[date | None] = mapped_column(Date)
    source_name: Mapped[str | None] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(1000))
    application_url: Mapped[str | None] = mapped_column(String(1000))
    date_discovered: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_verified: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(ListingStatus, values_callable=lambda e: [e.value for e in e]),
        default=ListingStatus.ACTIVE,
    )
    dedup_hash: Mapped[str | None] = mapped_column(String(64))
    raw_data: Mapped[dict | None] = mapped_column(JSON)


class JobMatch(Base, TimestampMixin):
    __tablename__ = "job_matches"
    __table_args__ = (
        Index("ix_job_match_listing", "job_listing_id"),
        Index("ix_job_match_score", "overall_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_listing_id: Mapped[int] = mapped_column(
        ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(30))  # strong/worth_considering/stretch/low
    dimensions: Mapped[dict | None] = mapped_column(JSON, default=dict)
    strong_matches: Mapped[list | None] = mapped_column(JSON, default=list)
    partial_matches: Mapped[list | None] = mapped_column(JSON, default=list)
    missing_requirements: Mapped[list | None] = mapped_column(JSON, default=list)
    potential_disqualifiers: Mapped[list | None] = mapped_column(JSON, default=list)
    unknown_items: Mapped[list | None] = mapped_column(JSON, default=list)
    factors: Mapped[list | None] = mapped_column(JSON, default=list)
    narrative: Mapped[str | None] = mapped_column(Text)
    weights_snapshot: Mapped[dict | None] = mapped_column(JSON)

    listing = relationship("JobListing")


class JobSearch(Base, TimestampMixin):
    __tablename__ = "job_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    query: Mapped[str | None] = mapped_column(String(400))
    filters: Mapped[dict | None] = mapped_column(JSON, default=dict)
    source_ids: Mapped[list | None] = mapped_column(JSON, default=list)
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_cron: Mapped[str | None] = mapped_column(String(80))
    last_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_match_score: Mapped[float | None] = mapped_column(Float, default=0.0)
