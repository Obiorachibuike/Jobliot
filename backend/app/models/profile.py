"""Career profile models: the verified source of truth about the user.

Every fact that originates from anywhere other than direct user input
carries a ``verification_status`` and a ``provenance`` tag so the
application can distinguish confirmed facts from suggestions.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
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


class VerificationStatus(str, Enum):
    USER_CONFIRMED = "user_confirmed"
    IMPORTED_PENDING = "imported_pending"
    EXTRACTED = "extracted"
    AI_SUGGESTED = "ai_suggested"
    UNVERIFIED = "unverified"
    OUTDATED = "outdated"


PROVENANCE_CHOICES = (
    "user",
    "onboarding",
    "cv_import",
    "ai_suggestion",
    "manual_entry",
)


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # identity
    full_name: Mapped[str | None] = mapped_column(String(200))
    preferred_name: Mapped[str | None] = mapped_column(String(120))
    headline: Mapped[str | None] = mapped_column(String(240))
    summary: Mapped[str | None] = mapped_column(Text)
    # contact (private by default)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(60))
    location_city: Mapped[str | None] = mapped_column(String(120))
    location_country: Mapped[str | None] = mapped_column(String(120))
    # public CV fields
    website: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    other_profiles: Mapped[dict | list | None] = mapped_column(JSON, default=list)
    # onboarding
    objectives: Mapped[list | None] = mapped_column(JSON, default=list)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)
    timezone: Mapped[str | None] = mapped_column(String(64))
    locale: Mapped[str | None] = mapped_column(String(16))

    experience = relationship("WorkExperience", back_populates="profile", cascade="all, delete-orphan", order_by="WorkExperience.sort_order")
    education = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="profile", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="profile", cascade="all, delete-orphan")
    preferences = relationship(
        "CareerPreference", back_populates="profile", uselist=False, cascade="all, delete-orphan"
    )
    writing_style = relationship(
        "WritingStyleProfile", back_populates="profile", uselist=False, cascade="all, delete-orphan"
    )
    master_cv = relationship("MasterCV", back_populates="profile", uselist=False, cascade="all, delete-orphan")


class WorkExperience(Base, TimestampMixin):
    __tablename__ = "work_experience"
    __table_args__ = (Index("ix_work_experience_profile", "profile_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    organization: Mapped[str] = mapped_column(String(240), nullable=False)
    job_title: Mapped[str] = mapped_column(String(240), nullable=False)
    employment_type: Mapped[str | None] = mapped_column(String(60))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    responsibilities: Mapped[list | None] = mapped_column(JSON, default=list)
    achievements: Mapped[list | None] = mapped_column(JSON, default=list)
    technologies: Mapped[list | None] = mapped_column(JSON, default=list)
    team_leadership: Mapped[str | None] = mapped_column(Text)
    outcomes: Mapped[str | None] = mapped_column(Text)
    related_projects: Mapped[list | None] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(
        SAEnum(VerificationStatus, values_callable=lambda e: [e.value for e in e]),
        default=VerificationStatus.USER_CONFIRMED,
    )
    provenance: Mapped[str | None] = mapped_column(String(40), default="user")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    profile = relationship("UserProfile", back_populates="experience")


class Education(Base, TimestampMixin):
    __tablename__ = "education"
    __table_args__ = (Index("ix_education_profile", "profile_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    institution: Mapped[str] = mapped_column(String(300), nullable=False)
    qualification: Mapped[str | None] = mapped_column(String(200))
    field_of_study: Mapped[str | None] = mapped_column(String(240))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    relevant_coursework: Mapped[list | None] = mapped_column(JSON, default=list)
    academic_achievements: Mapped[list | None] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        SAEnum(VerificationStatus, values_callable=lambda e: [e.value for e in e]),
        default=VerificationStatus.USER_CONFIRMED,
    )
    provenance: Mapped[str | None] = mapped_column(String(40), default="user")

    profile = relationship("UserProfile", back_populates="education")


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"
    __table_args__ = (Index("ix_skill_profile", "profile_id"), Index("ix_skill_name", "name"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    proficiency: Mapped[str | None] = mapped_column(String(40))  # e.g. beginner/intermediate/advanced/expert
    years_experience: Mapped[float | None] = mapped_column(Integer, nullable=True)
    last_used: Mapped[date | None] = mapped_column(Date)
    supporting_project: Mapped[str | None] = mapped_column(String(240))
    confidence: Mapped[str | None] = mapped_column(String(40))  # low/medium/high
    evidence: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        SAEnum(VerificationStatus, values_callable=lambda e: [e.value for e in e]),
        default=VerificationStatus.USER_CONFIRMED,
    )
    provenance: Mapped[str | None] = mapped_column(String(40), default="user")

    profile = relationship("UserProfile", back_populates="skills")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_project_profile", "profile_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    problem_solved: Mapped[str | None] = mapped_column(Text)
    technologies: Mapped[list | None] = mapped_column(JSON, default=list)
    responsibilities: Mapped[list | None] = mapped_column(JSON, default=list)
    outcomes: Mapped[str | None] = mapped_column(Text)
    repository_url: Mapped[str | None] = mapped_column(String(500))
    live_demo_url: Mapped[str | None] = mapped_column(String(500))
    screenshots: Mapped[list | None] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(
        SAEnum(VerificationStatus, values_callable=lambda e: [e.value for e in e]),
        default=VerificationStatus.USER_CONFIRMED,
    )
    provenance: Mapped[str | None] = mapped_column(String(40), default="user")

    profile = relationship("UserProfile", back_populates="projects")


class Certification(Base, TimestampMixin):
    __tablename__ = "certifications"
    __table_args__ = (Index("ix_certification_profile", "profile_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    issuing_organization: Mapped[str | None] = mapped_column(String(300))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    credential_id: Mapped[str | None] = mapped_column(String(200))
    verification_status: Mapped[str] = mapped_column(
        SAEnum(VerificationStatus, values_callable=lambda e: [e.value for e in e]),
        default=VerificationStatus.USER_CONFIRMED,
    )
    provenance: Mapped[str | None] = mapped_column(String(40), default="user")

    profile = relationship("UserProfile", back_populates="certifications")


class Achievement(Base, TimestampMixin):
    __tablename__ = "achievements"
    __table_args__ = (Index("ix_achievement_profile", "profile_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), default="award")  # award/publication/volunteering/research/other
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    date: Mapped[date | None] = mapped_column(Date)
    organization: Mapped[str | None] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(String(500))
    verification_status: Mapped[str] = mapped_column(
        SAEnum(VerificationStatus, values_callable=lambda e: [e.value for e in e]),
        default=VerificationStatus.USER_CONFIRMED,
    )
    provenance: Mapped[str | None] = mapped_column(String(40), default="user")

    profile = relationship("UserProfile", back_populates="achievements")


class CareerPreference(Base, TimestampMixin):
    __tablename__ = "career_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    desired_job_titles: Mapped[list | None] = mapped_column(JSON, default=list)
    target_industries: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_countries: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_cities: Mapped[list | None] = mapped_column(JSON, default=list)
    workplace_types: Mapped[list | None] = mapped_column(JSON, default=list)  # remote/hybrid/onsite
    employment_types: Mapped[list | None] = mapped_column(JSON, default=list)  # full-time/contract/...
    experience_level: Mapped[str | None] = mapped_column(String(60))
    salary_expectation_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_expectation_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minimum_acceptable_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8))
    work_authorization: Mapped[str | None] = mapped_column(Text)
    relocation_preference: Mapped[str | None] = mapped_column(String(60))
    company_sizes: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_technologies: Mapped[list | None] = mapped_column(JSON, default=list)
    avoid_technologies: Mapped[list | None] = mapped_column(JSON, default=list)
    avoid_industries: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_sources: Mapped[list | None] = mapped_column(JSON, default=list)
    max_daily_recommendations: Mapped[int | None] = mapped_column(Integer, default=10)

    profile = relationship("UserProfile", back_populates="preferences")


class WritingStyleProfile(Base, TimestampMixin):
    __tablename__ = "writing_style_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    formality: Mapped[str | None] = mapped_column(String(30))  # formal/balanced/conversational
    detail_level: Mapped[str | None] = mapped_column(String(30))  # concise/standard/detailed
    confidence_tone: Mapped[str | None] = mapped_column(String(30))  # confident/balanced/understated
    explanation_style: Mapped[str | None] = mapped_column(String(30))  # technical/accessible
    cv_style: Mapped[str | None] = mapped_column(String(40))
    cover_letter_length: Mapped[str | None] = mapped_column(String(30))  # concise/standard/detailed
    uses_first_person: Mapped[bool] = mapped_column(Boolean, default=True)
    disliked_phrases: Mapped[list | None] = mapped_column(JSON, default=list)
    directness: Mapped[str | None] = mapped_column(String(30))  # direct/diplomatic
    chosen_examples: Mapped[list | None] = mapped_column(JSON, default=list)
    writing_samples: Mapped[list | None] = mapped_column(JSON, default=list)
    extracted_preferences: Mapped[dict | None] = mapped_column(JSON, default=dict)

    profile = relationship("UserProfile", back_populates="writing_style")
