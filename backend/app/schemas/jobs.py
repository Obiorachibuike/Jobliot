"""Schemas for job discovery, URL import, and suitability matching."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobSourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    config: dict | None = None
    enabled: bool
    health_status: str | None = None
    last_checked: datetime | None = None
    error_message: str | None = None
    requires_api_key: bool = False

    model_config = {"from_attributes": True}


class JobSourceCreate(BaseModel):
    name: str
    source_type: str
    config: dict | None = None
    enabled: bool = True


class JobListingFilters(BaseModel):
    title: str | None = None
    keywords: str | None = None
    country: str | None = None
    city: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    industry: str | None = None
    company: str | None = None
    technology: str | None = None
    source: str | None = None
    published_since_days: int | None = None
    min_match_score: float | None = None
    status: str | None = None
    q: str | None = None


class JobListingOut(BaseModel):
    id: int
    title: str
    company: str
    location: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    description: str | None = None
    requirements: list | None = None
    preferred_qualifications: list | None = None
    publication_date: date | None = None
    closing_date: date | None = None
    source_name: str | None = None
    url: str | None = None
    application_url: str | None = None
    date_discovered: datetime
    last_verified: datetime | None = None
    status: str
    has_match: bool = False
    match_score: float | None = None
    match_category: str | None = None

    model_config = {"from_attributes": True}


class ManualJobCreate(BaseModel):
    title: str
    company: str
    location: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    description: str | None = None
    requirements: list[str] | None = None
    preferred_qualifications: list[str] | None = None
    publication_date: date | None = None
    closing_date: date | None = None
    application_url: str | None = None


class JobUrlImportRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2000)


class JobUrlImportResult(BaseModel):
    ok: bool
    extracted: dict | None = None
    warnings: list[str] = []
    error: str | None = None


class DimensionResult(BaseModel):
    name: str
    label: str
    score: float
    weight: float
    status: str  # match/partial/missing/unknown
    evidence: list[str] = []
    details: str | None = None


class MatchReportOut(BaseModel):
    job_listing_id: int
    overall_score: float
    category: str
    dimensions: list[DimensionResult] = []
    strong_matches: list[str] = []
    partial_matches: list[str] = []
    missing_requirements: list[str] = []
    potential_disqualifiers: list[str] = []
    unknown_items: list[str] = []
    factors: list[str] = []
    narrative: str | None = None
    weights: dict | None = None


class SavedSearchBase(BaseModel):
    name: str
    query: str | None = None
    filters: dict | None = None
    source_ids: list[int] | None = None
    schedule_enabled: bool = False
    schedule_cron: str | None = None
    min_match_score: float | None = 0.0


class SavedSearchOut(SavedSearchBase):
    id: int
    is_active: bool
    last_run: datetime | None = None
    next_run: datetime | None = None

    model_config = {"from_attributes": True}


class MatchWeights(BaseModel):
    required_skills: float = 0.30
    preferred_skills: float = 0.10
    experience: float = 0.16
    education: float = 0.06
    certifications: float = 0.05
    projects: float = 0.08
    seniority: float = 0.09
    location: float = 0.06
    employment_type: float = 0.04
    salary: float = 0.03
    portfolio: float = 0.03

    @property
    def total(self) -> float:
        return sum(
            [
                self.required_skills,
                self.preferred_skills,
                self.experience,
                self.education,
                self.certifications,
                self.projects,
                self.seniority,
                self.location,
                self.employment_type,
                self.salary,
                self.portfolio,
            ]
        )


class MatchCategory(str, Enum):
    STRONG = "strong_match"
    CONSIDER = "worth_considering"
    STRETCH = "stretch_opportunity"
    LOW = "low_match"
