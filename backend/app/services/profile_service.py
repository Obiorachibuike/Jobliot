"""Career profile persistence and onboarding state management.

All profile mutations flow through this service so verification
statuses and provenance are applied consistently.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.profile import (
    Achievement,
    CareerPreference,
    Certification,
    Education,
    Project,
    Skill,
    UserProfile,
    VerificationStatus,
    WorkExperience,
    WritingStyleProfile,
)
from app.schemas.profile import (
    AchievementBase,
    CareerPreferenceBase,
    CertificationBase,
    EducationBase,
    OnboardingStateOut,
    ProjectBase,
    SkillBase,
    UserProfileBase,
    WorkExperienceBase,
    WritingStyleBase,
)

# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------

def get_or_create_profile(session: Session) -> UserProfile:
    profile = session.query(UserProfile).first()
    if profile is None:
        profile = UserProfile()
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def update_profile(session: Session, profile: UserProfile, data: UserProfileBase) -> UserProfile:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


def get_onboarding_state(session: Session) -> OnboardingStateOut:
    profile = session.query(UserProfile).first()
    if profile is None:
        return OnboardingStateOut(
            profile_exists=False,
            onboarding_completed=False,
            onboarding_step=0,
            completed_steps=[],
            has_profile_data=False,
        )
    completed: list[int] = []
    if profile.full_name or profile.headline:
        completed.append(2)
    if profile.experience:
        completed.append(4)
    if profile.education:
        completed.append(3)
    if profile.skills:
        completed.append(5)
    if profile.projects:
        completed.append(6)
    if profile.certifications or profile.achievements:
        completed.append(7)
    if profile.preferences is not None:
        completed.append(8)
    if profile.writing_style is not None:
        completed.append(9)
    if profile.master_cv:  # type: ignore[attr-defined]
        completed.append(10)
    if profile.onboarding_completed:
        completed.append(11)
    return OnboardingStateOut(
        profile_exists=True,
        onboarding_completed=profile.onboarding_completed,
        onboarding_step=profile.onboarding_step,
        completed_steps=completed,
        has_profile_data=bool(
            profile.full_name
            or profile.headline
            or profile.experience
            or profile.skills
        ),
        objectives=profile.objectives or [],
    )


ONBOARDING_STEP_FIELDS = {
    1: ["objectives"],
    2: [
        "full_name", "preferred_name", "headline", "summary", "email", "phone",
        "location_city", "location_country", "website", "linkedin_url",
        "github_url", "portfolio_url", "other_profiles", "timezone",
    ],
    3: [],  # education saved via entity endpoints
    4: [],  # experience saved via entity endpoints
    5: [],  # skills saved via entity endpoints
    6: [],  # projects saved via entity endpoints
    7: [],  # certifications/achievements via entity endpoints
    8: ["preferences"],
    9: ["writing_style"],
    10: [],  # CV import handled separately
    11: [],  # review step
}


def save_onboarding_step(session: Session, step: int, data: dict) -> dict:
    profile = get_or_create_profile(session)
    profile.onboarding_step = max(profile.onboarding_step or 0, step)
    result: dict[str, Any] = {"saved": True, "step": step}

    if step == 1 and "objectives" in data:
        objectives = data.get("objectives") or []
        profile.objectives = [str(o)[:80] for o in objectives][:12]
        result["objectives"] = profile.objectives
    elif step == 2:
        allowed = ONBOARDING_STEP_FIELDS[2]
        payload = {k: v for k, v in data.items() if k in allowed}
        for key, value in payload.items():
            setattr(profile, key, value)
    elif step == 8 and "preferences" in data:
        prefs = data["preferences"] or {}
        existing = profile.preferences
        if existing is None:
            existing = CareerPreference(profile_id=profile.id)
            session.add(existing)
        for key, value in prefs.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        result["preferences_saved"] = True
    elif step == 9 and "writing_style" in data:
        style = data["writing_style"] or {}
        existing = profile.writing_style
        if existing is None:
            existing = WritingStyleProfile(profile_id=profile.id)
            session.add(existing)
        for key, value in style.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        result["writing_style_saved"] = True

    session.commit()
    session.refresh(profile)
    return result


def complete_onboarding(session: Session) -> UserProfile:
    profile = get_or_create_profile(session)
    profile.onboarding_completed = True
    profile.onboarding_step = 11
    session.commit()
    session.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# generic entity CRUD helpers
# ---------------------------------------------------------------------------

def _get_or_404(session: Session, model, entity_id: int):
    entity = session.get(model, entity_id)
    if entity is None:
        raise LookupError(f"{model.__tablename__} {entity_id} not found")
    return entity


def create_entity(session: Session, model, payload: dict, profile_id: int):
    entity = model(profile_id=profile_id, **payload)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


def update_entity(session: Session, model, entity_id: int, payload: dict):
    entity = _get_or_404(session, model, entity_id)
    for key, value in payload.items():
        if hasattr(entity, key) and key not in ("id", "profile_id", "created_at"):
            setattr(entity, key, value)
    session.commit()
    session.refresh(entity)
    return entity


def delete_entity(session: Session, model, entity_id: int) -> bool:
    entity = _get_or_404(session, model, entity_id)
    session.delete(entity)
    session.commit()
    return True


def list_entities(session: Session, model, profile_id: int, ordering: str = "id"):
    query = session.query(model).filter(model.profile_id == profile_id)
    if ordering == "desc":
        query = query.order_by(model.id.desc())
    else:
        query = query.order_by(model.id.asc())
    return query.all()


# ---------------------------------------------------------------------------
# verification helpers
# ---------------------------------------------------------------------------

def can_promote_to_confirmed(current: str, proposed: str) -> bool:
    """Only user actions may promote a fact to user_confirmed."""
    return proposed == VerificationStatus.USER_CONFIRMED.value


def apply_imported_status(entity, fields: list[str]) -> None:
    """Mark imported fields as pending confirmation (never auto-verified)."""
    entity.verification_status = VerificationStatus.IMPORTED_PENDING.value
    entity.provenance = "cv_import"


# ---------------------------------------------------------------------------
# CV text extraction
# ---------------------------------------------------------------------------

def extract_text_from_docx(content_bytes: bytes) -> str:
    from docx import Document as DocxDocument

    import io

    doc = DocxDocument(io.BytesIO(content_bytes))
    lines: list[str] = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            lines.append(text)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                lines.append(" | ".join(cells))
    return "\n".join(lines)


def extract_text_from_pdf(content_bytes: bytes) -> str:
    from pypdf import PdfReader

    import io

    reader = PdfReader(io.BytesIO(content_bytes))
    pages: list[str] = []
    for page in reader.pages[:20]:  # bound the work
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def extract_cv_text(filename: str, content_bytes: bytes) -> str:
    lowered = filename.lower()
    if lowered.endswith(".docx"):
        return extract_text_from_docx(content_bytes)
    if lowered.endswith(".pdf"):
        return extract_text_from_pdf(content_bytes)
    if lowered.endswith(".txt") or lowered.endswith(".md"):
        return content_bytes.decode("utf-8", errors="replace")
    raise ValueError(
        f"Unsupported CV format for '{filename}'. Supported: PDF, DOCX, TXT."
    )


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().\-]{7,}\d)")
_URL_RE = re.compile(r"https?://[^\s]+")

_SECTION_HEADINGS = {
    "summary": r"(professional summary|profile|about me|career profile)",
    "experience": r"(work experience|experience|employment history|professional experience)",
    "education": r"(education|academic background|qualifications)",
    "skills": r"(skills|technical skills|core competencies|key skills)",
    "projects": r"(projects|project experience|portfolio|selected projects)",
    "certifications": r"(certifications|certificates|licenses|credentials)",
}


def parse_cv_sections(text: str) -> dict[str, list[str]]:
    """Split CV text into sections by common heading keywords."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections: dict[str, list[str]] = {key: [] for key in _SECTION_HEADINGS}
    current: str | None = None
    for line in lines:
        lowered = line.lower().rstrip(":")
        matched = None
        for key, pattern in _SECTION_HEADINGS.items():
            if re.fullmatch(pattern, lowered) or re.match(pattern + r"\b", lowered):
                matched = key
                break
        if matched:
            current = matched
            continue
        if current:
            sections[current].append(line)
    return sections


def extract_cv_structured(text: str) -> tuple[dict, list[str]]:
    """Heuristically extract structured CV data.

    Returns ``(extracted, uncertain_fields)``.  Extraction is
    deliberately conservative: anything not clearly parseable is
    listed as uncertain rather than guessed.
    """
    extracted: dict[str, Any] = {}
    uncertain: list[str] = []

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    emails = _EMAIL_RE.findall(text)
    phones = _PHONE_RE.findall(text)
    urls = _URL_RE.findall(text)

    name = lines[0] if lines else ""
    if name and len(name.split()) <= 5 and not any(
        ch.isdigit() for ch in name
    ):
        extracted["full_name"] = name
        uncertain.append("full_name")
    else:
        uncertain.append("full_name (could not detect a name line)")

    if emails:
        extracted["email"] = emails[0]
    if phones:
        extracted["phone"] = phones[0].strip()
        uncertain.append("phone")
    if urls:
        extracted["urls"] = list(dict.fromkeys(urls))[:6]
        uncertain.append("urls (profile links assumed)")

    sections = parse_cv_sections(text)
    if sections["summary"]:
        extracted["summary"] = " ".join(sections["summary"][:3])
        uncertain.append("summary")
    if sections["skills"]:
        skill_blob = " ".join(sections["skills"])
        skills = [s.strip() for s in re.split(r"[,\n•;]| and ", skill_blob) if s.strip()]
        extracted["skills"] = skills[:40]
        uncertain.append("skills (proficiency unknown)")
    if sections["experience"]:
        extracted["experience_raw"] = sections["experience"][:60]
        uncertain.append("experience (dates and roles must be confirmed)")
    if sections["education"]:
        extracted["education_raw"] = sections["education"][:20]
        uncertain.append("education")
    if sections["projects"]:
        extracted["projects_raw"] = sections["projects"][:20]
        uncertain.append("projects")
    if sections["certifications"]:
        extracted["certifications_raw"] = sections["certifications"][:10]
        uncertain.append("certifications")

    return extracted, uncertain
