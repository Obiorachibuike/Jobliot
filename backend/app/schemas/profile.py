"""Schemas for onboarding and the career knowledge base."""

from __future__ import annotations

from datetime import date as date_type
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.models.profile import VerificationStatus


class VerificationStatusOut(str, Enum):
    USER_CONFIRMED = "user_confirmed"
    IMPORTED_PENDING = "imported_pending"
    EXTRACTED = "extracted"
    AI_SUGGESTED = "ai_suggested"
    UNVERIFIED = "unverified"
    OUTDATED = "outdated"


# --------------------------------------------------------------------------- profile
class UserProfileBase(BaseModel):
    full_name: str | None = None
    preferred_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    email: str | None = None
    phone: str | None = None
    location_city: str | None = None
    location_country: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    other_profiles: list | None = None
    objectives: list[str] | None = None
    timezone: str | None = None
    locale: str | None = None


class UserProfileOut(UserProfileBase):
    id: int
    onboarding_completed: bool
    onboarding_step: int

    model_config = {"from_attributes": True}


class OnboardingStateOut(BaseModel):
    profile_exists: bool
    onboarding_completed: bool
    onboarding_step: int
    completed_steps: list[int]
    has_profile_data: bool
    objectives: list[str] = []


class OnboardingSaveRequest(BaseModel):
    step: int = Field(ge=1, le=11)
    data: dict


class OnboardingCompleteRequest(BaseModel):
    confirm_incomplete_allowed: bool = True


# --------------------------------------------------------------------------- entities
class WorkExperienceBase(BaseModel):
    organization: str
    job_title: str
    employment_type: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None
    is_current: bool = False
    responsibilities: list[str] | None = None
    achievements: list[str] | None = None
    technologies: list[str] | None = None
    team_leadership: str | None = None
    outcomes: str | None = None
    related_projects: list[str] | None = None
    verification_status: VerificationStatus = VerificationStatus.USER_CONFIRMED
    provenance: str | None = "user"


class WorkExperienceOut(WorkExperienceBase):
    id: int

    model_config = {"from_attributes": True}


class EducationBase(BaseModel):
    institution: str
    qualification: str | None = None
    field_of_study: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None
    is_current: bool = False
    relevant_coursework: list[str] | None = None
    academic_achievements: list[str] | None = None
    notes: str | None = None
    verification_status: VerificationStatus = VerificationStatus.USER_CONFIRMED
    provenance: str | None = "user"


class EducationOut(EducationBase):
    id: int

    model_config = {"from_attributes": True}


class SkillBase(BaseModel):
    name: str
    category: str | None = None
    proficiency: str | None = None
    years_experience: int | None = None
    last_used: date_type | None = None
    supporting_project: str | None = None
    confidence: str | None = None
    evidence: str | None = None
    verification_status: VerificationStatus = VerificationStatus.USER_CONFIRMED
    provenance: str | None = "user"


class SkillOut(SkillBase):
    id: int

    model_config = {"from_attributes": True}


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    problem_solved: str | None = None
    technologies: list[str] | None = None
    responsibilities: list[str] | None = None
    outcomes: str | None = None
    repository_url: str | None = None
    live_demo_url: str | None = None
    screenshots: list | None = None
    is_public: bool = True
    verification_status: VerificationStatus = VerificationStatus.USER_CONFIRMED
    provenance: str | None = "user"


class ProjectOut(ProjectBase):
    id: int

    model_config = {"from_attributes": True}


class CertificationBase(BaseModel):
    name: str
    issuing_organization: str | None = None
    issue_date: date_type | None = None
    expiry_date: date_type | None = None
    credential_url: str | None = None
    credential_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.USER_CONFIRMED
    provenance: str | None = "user"


class CertificationOut(CertificationBase):
    id: int

    model_config = {"from_attributes": True}


class AchievementBase(BaseModel):
    kind: str = "award"
    title: str
    description: str | None = None
    date: date_type | None = None
    organization: str | None = None
    url: str | None = None
    verification_status: VerificationStatus = VerificationStatus.USER_CONFIRMED
    provenance: str | None = "user"


class AchievementOut(AchievementBase):
    id: int

    model_config = {"from_attributes": True}


class CareerPreferenceBase(BaseModel):
    desired_job_titles: list[str] | None = None
    target_industries: list[str] | None = None
    preferred_countries: list[str] | None = None
    preferred_cities: list[str] | None = None
    workplace_types: list[str] | None = None
    employment_types: list[str] | None = None
    experience_level: str | None = None
    salary_expectation_min: int | None = None
    salary_expectation_max: int | None = None
    minimum_acceptable_salary: int | None = None
    currency: str | None = None
    work_authorization: str | None = None
    relocation_preference: str | None = None
    company_sizes: list[str] | None = None
    preferred_technologies: list[str] | None = None
    avoid_technologies: list[str] | None = None
    avoid_industries: list[str] | None = None
    preferred_sources: list[str] | None = None
    max_daily_recommendations: int | None = 10


class CareerPreferenceOut(CareerPreferenceBase):
    id: int

    model_config = {"from_attributes": True}


class WritingStyleBase(BaseModel):
    formality: str | None = None
    detail_level: str | None = None
    confidence_tone: str | None = None
    explanation_style: str | None = None
    cv_style: str | None = None
    cover_letter_length: str | None = None
    uses_first_person: bool = True
    disliked_phrases: list[str] | None = None
    directness: str | None = None
    chosen_examples: list[str] | None = None
    writing_samples: list[str] | None = None
    extracted_preferences: dict | None = None


class WritingStyleOut(WritingStyleBase):
    id: int

    model_config = {"from_attributes": True}


class CareerProfileOut(BaseModel):
    profile: UserProfileOut
    experience: list[WorkExperienceOut] = []
    education: list[EducationOut] = []
    skills: list[SkillOut] = []
    projects: list[ProjectOut] = []
    certifications: list[CertificationOut] = []
    achievements: list[AchievementOut] = []
    preferences: CareerPreferenceOut | None = None
    writing_style: WritingStyleOut | None = None


# --------------------------------------------------------------------------- CV import
class CVImportRequest(BaseModel):
    filename: str
    mime_type: str
    content_b64: str


class CVImportResult(BaseModel):
    extracted: dict
    uncertain_fields: list[str] = []
    warnings: list[str] = []


class CVImportConfirmRequest(BaseModel):
    approved: dict
    rejected_fields: list[str] = []
