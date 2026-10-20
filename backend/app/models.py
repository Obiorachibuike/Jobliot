from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
def now(): return datetime.now(timezone.utc)

class UserProfile(Base):
    __tablename__="user_profile"
    id:Mapped[int]=mapped_column(primary_key=True)
    full_name:Mapped[str]=mapped_column(String(160),default="")
    headline:Mapped[str]=mapped_column(String(240),default="")
    email:Mapped[str]=mapped_column(String(200),default="")
    phone:Mapped[str]=mapped_column(String(60),default="")
    city:Mapped[str]=mapped_column(String(120),default=""); country:Mapped[str]=mapped_column(String(120),default="")
    linkedin:Mapped[str]=mapped_column(String(300),default=""); github:Mapped[str]=mapped_column(String(300),default=""); portfolio:Mapped[str]=mapped_column(String(300),default="")
    summary:Mapped[str]=mapped_column(Text,default=""); objectives:Mapped[list]=mapped_column(JSON,default=list)
    show_on_cv:Mapped[dict]=mapped_column(JSON,default=dict)
    preferences:Mapped[dict]=mapped_column(JSON,default=dict); writing_style:Mapped[dict]=mapped_column(JSON,default=dict)
    onboarding_step:Mapped[int]=mapped_column(Integer,default=0); onboarding_complete:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)

class WorkExperience(Base):
    __tablename__="work_experience"
    id:Mapped[int]=mapped_column(primary_key=True)
    organization:Mapped[str]=mapped_column(String(200)); title:Mapped[str]=mapped_column(String(200))
    employment_type:Mapped[str]=mapped_column(String(60),default="Full-time"); start_date:Mapped[str]=mapped_column(String(20),default=""); end_date:Mapped[str]=mapped_column(String(20),default="")
    current:Mapped[bool]=mapped_column(Boolean,default=False); location:Mapped[str]=mapped_column(String(160),default="")
    description:Mapped[str]=mapped_column(Text,default=""); achievements:Mapped[list]=mapped_column(JSON,default=list); tools:Mapped[list]=mapped_column(JSON,default=list)
    verification_status:Mapped[str]=mapped_column(String(40),default="user_confirmed"); sort_order:Mapped[int]=mapped_column(Integer,default=0)

class Education(Base):
    __tablename__="education"
    id:Mapped[int]=mapped_column(primary_key=True)
    institution:Mapped[str]=mapped_column(String(200)); qualification:Mapped[str]=mapped_column(String(200)); field:Mapped[str]=mapped_column(String(200),default="")
    start_date:Mapped[str]=mapped_column(String(20),default=""); end_date:Mapped[str]=mapped_column(String(20),default=""); current:Mapped[bool]=mapped_column(Boolean,default=False)
    coursework:Mapped[list]=mapped_column(JSON,default=list); achievements:Mapped[str]=mapped_column(Text,default="")
    verification_status:Mapped[str]=mapped_column(String(40),default="user_confirmed")

class Skill(Base):
    __tablename__="skills"; __table_args__=(UniqueConstraint("name","category"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120),index=True); category:Mapped[str]=mapped_column(String(120),default="General")
    proficiency:Mapped[str]=mapped_column(String(40),default="Intermediate"); years:Mapped[float]=mapped_column(Float,nullable=True)
    last_used:Mapped[str]=mapped_column(String(20),default=""); evidence:Mapped[str]=mapped_column(Text,default="")
    verification_status:Mapped[str]=mapped_column(String(40),default="user_confirmed")

class Project(Base):
    __tablename__="projects"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(200)); description:Mapped[str]=mapped_column(Text,default=""); problem:Mapped[str]=mapped_column(Text,default="")
    technologies:Mapped[list]=mapped_column(JSON,default=list); responsibilities:Mapped[str]=mapped_column(Text,default=""); outcomes:Mapped[str]=mapped_column(Text,default="")
    repo_url:Mapped[str]=mapped_column(String(400),default=""); demo_url:Mapped[str]=mapped_column(String(400),default=""); is_public:Mapped[bool]=mapped_column(Boolean,default=True)
    verification_status:Mapped[str]=mapped_column(String(40),default="user_confirmed")

class Certification(Base):
    __tablename__="certifications"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(200)); issuer:Mapped[str]=mapped_column(String(200),default=""); issue_date:Mapped[str]=mapped_column(String(20),default=""); expiry_date:Mapped[str]=mapped_column(String(20),default="")
    credential_url:Mapped[str]=mapped_column(String(400),default=""); credential_id:Mapped[str]=mapped_column(String(120),default=""); verification_status:Mapped[str]=mapped_column(String(40),default="user_confirmed")

class Achievement(Base):
    __tablename__="achievements"
    id:Mapped[int]=mapped_column(primary_key=True)
    kind:Mapped[str]=mapped_column(String(60),default="award"); title:Mapped[str]=mapped_column(String(240)); description:Mapped[str]=mapped_column(Text,default=""); date:Mapped[str]=mapped_column(String(20),default=""); verification_status:Mapped[str]=mapped_column(String(40),default="user_confirmed")

class JobListing(Base):
    __tablename__="job_listings"
    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(240),index=True); company:Mapped[str]=mapped_column(String(200),index=True)
    location:Mapped[str]=mapped_column(String(200),default=""); workplace_type:Mapped[str]=mapped_column(String(40),default=""); employment_type:Mapped[str]=mapped_column(String(60),default="")
    salary_min:Mapped[float]=mapped_column(Float,nullable=True); salary_max:Mapped[float]=mapped_column(Float,nullable=True); salary_currency:Mapped[str]=mapped_column(String(10),default="")
    description:Mapped[str]=mapped_column(Text,default=""); requirements:Mapped[list]=mapped_column(JSON,default=list); skills:Mapped[list]=mapped_column(JSON,default=list)
    source:Mapped[str]=mapped_column(String(80),default="Manual",index=True); source_id:Mapped[str]=mapped_column(String(300),default="",index=True)
    url:Mapped[str]=mapped_column(String(600),default=""); normalized_url:Mapped[str]=mapped_column(String(600),default="",index=True)
    fingerprint:Mapped[str]=mapped_column(String(64),default="",unique=True,index=True)
    published_at:Mapped[str]=mapped_column(String(40),default=""); closing_date:Mapped[str]=mapped_column(String(40),default="")
    status:Mapped[str]=mapped_column(String(30),default="unverified"); experience_level:Mapped[str]=mapped_column(String(60),default=""); industry:Mapped[str]=mapped_column(String(120),default="")
    discovered_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); last_verified_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=True)
    match:Mapped[dict]=mapped_column(JSON,default=dict)

class SavedSearch(Base):
    __tablename__="saved_searches"
    id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(160)); filters:Mapped[dict]=mapped_column(JSON,default=dict)
    schedule:Mapped[dict]=mapped_column(JSON,default=dict); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Document(Base):
    __tablename__="documents"
    id:Mapped[int]=mapped_column(primary_key=True)
    kind:Mapped[str]=mapped_column(String(30),index=True)  # master_cv, tailored_cv, cover_letter
    title:Mapped[str]=mapped_column(String(240)); job_id:Mapped[int]=mapped_column(ForeignKey("job_listings.id",ondelete="SET NULL"),nullable=True)
    template:Mapped[str]=mapped_column(String(60),default="ats"); status:Mapped[str]=mapped_column(String(40),default="draft")
    content:Mapped[dict]=mapped_column(JSON,default=dict); plain_text:Mapped[str]=mapped_column(Text,default="")
    strategy:Mapped[dict]=mapped_column(JSON,default=dict); review:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    versions:Mapped[list["DocumentVersion"]]=relationship(back_populates="document",cascade="all, delete-orphan",order_by="DocumentVersion.version")

class DocumentVersion(Base):
    __tablename__="document_versions"
    id:Mapped[int]=mapped_column(primary_key=True); document_id:Mapped[int]=mapped_column(ForeignKey("documents.id",ondelete="CASCADE"),index=True)
    version:Mapped[int]=mapped_column(Integer,default=1); plain_text:Mapped[str]=mapped_column(Text,default=""); content:Mapped[dict]=mapped_column(JSON,default=dict)
    note:Mapped[str]=mapped_column(String(300),default=""); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    document:Mapped["Document"]=relationship(back_populates="versions")

class Application(Base):
    __tablename__="applications"
    id:Mapped[int]=mapped_column(primary_key=True)
    job_id:Mapped[int]=mapped_column(ForeignKey("job_listings.id",ondelete="SET NULL"),nullable=True)
    company:Mapped[str]=mapped_column(String(200),index=True); title:Mapped[str]=mapped_column(String(240))
    status:Mapped[str]=mapped_column(String(60),default="Saved",index=True); source:Mapped[str]=mapped_column(String(80),default="Manual")
    application_url:Mapped[str]=mapped_column(String(600),default=""); deadline:Mapped[str]=mapped_column(String(40),default=""); date_applied:Mapped[str]=mapped_column(String(40),default="")
    cv_document_id:Mapped[int]=mapped_column(Integer,nullable=True); cover_letter_id:Mapped[int]=mapped_column(Integer,nullable=True)
    recruiter_name:Mapped[str]=mapped_column(String(160),default=""); recruiter_email:Mapped[str]=mapped_column(String(200),default="")
    interview_dates:Mapped[list]=mapped_column(JSON,default=list); follow_up_date:Mapped[str]=mapped_column(String(40),default="")
    notes:Mapped[str]=mapped_column(Text,default=""); outcome:Mapped[str]=mapped_column(String(60),default=""); feedback:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    events:Mapped[list["ApplicationEvent"]]=relationship(back_populates="application",cascade="all, delete-orphan",order_by="ApplicationEvent.created_at")

class ApplicationEvent(Base):
    __tablename__="application_events"
    id:Mapped[int]=mapped_column(primary_key=True); application_id:Mapped[int]=mapped_column(ForeignKey("applications.id",ondelete="CASCADE"),index=True)
    event_type:Mapped[str]=mapped_column(String(60)); detail:Mapped[str]=mapped_column(Text,default=""); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    application:Mapped["Application"]=relationship(back_populates="events")

class InterviewSession(Base):
    __tablename__="interview_sessions"
    id:Mapped[int]=mapped_column(primary_key=True); job_id:Mapped[int]=mapped_column(ForeignKey("job_listings.id",ondelete="SET NULL"),nullable=True)
    title:Mapped[str]=mapped_column(String(240)); questions:Mapped[list]=mapped_column(JSON,default=list); answers:Mapped[list]=mapped_column(JSON,default=list)
    summary:Mapped[dict]=mapped_column(JSON,default=dict); status:Mapped[str]=mapped_column(String(30),default="in_progress"); notes:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Reminder(Base):
    __tablename__="reminders"
    id:Mapped[int]=mapped_column(primary_key=True); title:Mapped[str]=mapped_column(String(240)); kind:Mapped[str]=mapped_column(String(60),default="follow_up")
    due_at:Mapped[str]=mapped_column(String(60),index=True); timezone:Mapped[str]=mapped_column(String(80),default="UTC"); application_id:Mapped[int]=mapped_column(Integer,nullable=True)
    done:Mapped[bool]=mapped_column(Boolean,default=False); notes:Mapped[str]=mapped_column(Text,default="")

class BackgroundTask(Base):
    __tablename__="background_tasks"
    id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(200)); kind:Mapped[str]=mapped_column(String(60))
    status:Mapped[str]=mapped_column(String(30),default="queued",index=True); progress:Mapped[float]=mapped_column(Float,nullable=True); detail:Mapped[str]=mapped_column(Text,default=""); result:Mapped[dict]=mapped_column(JSON,default=dict)
    started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=True); finished_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class AIProviderConfig(Base):
    __tablename__="ai_provider_config"
    id:Mapped[int]=mapped_column(primary_key=True); provider:Mapped[str]=mapped_column(String(40),default="none"); model:Mapped[str]=mapped_column(String(160),default="")
    endpoint:Mapped[str]=mapped_column(String(400),default=""); temperature:Mapped[float]=mapped_column(Float,default=0.3); max_tokens:Mapped[int]=mapped_column(Integer,default=2048)
    timeout_seconds:Mapped[int]=mapped_column(Integer,default=60); max_retries:Mapped[int]=mapped_column(Integer,default=2)
    task_models:Mapped[dict]=mapped_column(JSON,default=dict); monthly_token_budget:Mapped[int]=mapped_column(Integer,nullable=True); has_api_key:Mapped[bool]=mapped_column(Boolean,default=False)

class AIUsageRecord(Base):
    __tablename__="ai_usage"
    id:Mapped[int]=mapped_column(primary_key=True); provider:Mapped[str]=mapped_column(String(40)); model:Mapped[str]=mapped_column(String(160)); task:Mapped[str]=mapped_column(String(80))
    prompt_chars:Mapped[int]=mapped_column(Integer,default=0); completion_chars:Mapped[int]=mapped_column(Integer,default=0); success:Mapped[bool]=mapped_column(Boolean,default=True); error:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class AppSettings(Base):
    __tablename__="app_settings"
    id:Mapped[int]=mapped_column(primary_key=True); key:Mapped[str]=mapped_column(String(120),unique=True); value:Mapped[dict]=mapped_column(JSON,default=dict)
