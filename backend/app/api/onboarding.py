"""Onboarding and career-profile API."""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.profile import UserProfile
from app.schemas.profile import (
    AchievementBase,
    CareerPreferenceBase,
    CertificationBase,
    CVImportConfirmRequest,
    CVImportRequest,
    CVImportResult,
    EducationBase,
    OnboardingCompleteRequest,
    OnboardingSaveRequest,
    OnboardingStateOut,
    ProjectBase,
    SkillBase,
    UserProfileBase,
    UserProfileOut,
    WorkExperienceBase,
    WritingStyleBase,
)
from app.services import profile_service
from app.services.profile_service import (
    create_entity,
    delete_entity,
    extract_cv_structured,
    extract_cv_text,
    list_entities,
    update_entity,
)

router = APIRouter(prefix="/api/v1", dependencies=[TokenDep])


def _get_profile(session: Session) -> UserProfile:
    return profile_service.get_or_create_profile(session)


# --------------------------------------------------------------------------- onboarding
@router.get("/onboarding/state", response_model=OnboardingStateOut)
def onboarding_state(session: SessionDep):
    return profile_service.get_onboarding_state(session)


@router.post("/onboarding/step")
def onboarding_save_step(payload: OnboardingSaveRequest, session: SessionDep):
    return profile_service.save_onboarding_step(session, payload.step, payload.data)


@router.post("/onboarding/complete")
def onboarding_complete(_payload: OnboardingCompleteRequest, session: SessionDep):
    profile = profile_service.complete_onboarding(session)
    return {"ok": True, "profile_id": profile.id}


# --------------------------------------------------------------------------- profile
@router.get("/profile", response_model=UserProfileOut)
def get_profile(session: SessionDep):
    return _get_profile(session)


@router.patch("/profile", response_model=UserProfileOut)
def update_profile(payload: UserProfileBase, session: SessionDep):
    profile = _get_profile(session)
    return profile_service.update_profile(session, profile, payload)


# --------------------------------------------------------------------------- entities
from app.models.profile import WorkExperience  # noqa: E402


@router.get("/experience")
def list_experience(session: SessionDep):
    profile = _get_profile(session)
    return list_entities(session, WorkExperience, profile.id)


@router.post("/experience")
def create_experience(payload: WorkExperienceBase, session: SessionDep):
    profile = _get_profile(session)
    return create_entity(session, WorkExperience, payload.model_dump(), profile.id)


@router.patch("/experience/{entity_id}")
def update_experience(entity_id: int, payload: dict, session: SessionDep):
    return update_entity(session, WorkExperience, entity_id, payload)


@router.delete("/experience/{entity_id}")
def delete_experience(entity_id: int, session: SessionDep):
    delete_entity(session, WorkExperience, entity_id)
    return {"ok": True}


from app.models.profile import (  # noqa: E402
    Achievement,
    Certification,
    Education,
    Project,
    Skill,
    WritingStyleProfile,
)


@router.get("/education")
def list_education(session: SessionDep):
    profile = _get_profile(session)
    return list_entities(session, Education, profile.id)


@router.post("/education")
def create_education(payload: EducationBase, session: SessionDep):
    profile = _get_profile(session)
    return create_entity(session, Education, payload.model_dump(), profile.id)


@router.patch("/education/{entity_id}")
def update_education(entity_id: int, payload: dict, session: SessionDep):
    return update_entity(session, Education, entity_id, payload)


@router.delete("/education/{entity_id}")
def delete_education(entity_id: int, session: SessionDep):
    delete_entity(session, Education, entity_id)
    return {"ok": True}


@router.get("/skills")
def list_skills(session: SessionDep):
    profile = _get_profile(session)
    return list_entities(session, Skill, profile.id)


@router.post("/skills")
def create_skill(payload: SkillBase, session: SessionDep):
    profile = _get_profile(session)
    return create_entity(session, Skill, payload.model_dump(), profile.id)


@router.patch("/skills/{entity_id}")
def update_skill(entity_id: int, payload: dict, session: SessionDep):
    return update_entity(session, Skill, entity_id, payload)


@router.delete("/skills/{entity_id}")
def delete_skill(entity_id: int, session: SessionDep):
    delete_entity(session, Skill, entity_id)
    return {"ok": True}


@router.get("/projects")
def list_projects(session: SessionDep):
    profile = _get_profile(session)
    return list_entities(session, Project, profile.id)


@router.post("/projects")
def create_project(payload: ProjectBase, session: SessionDep):
    profile = _get_profile(session)
    return create_entity(session, Project, payload.model_dump(), profile.id)


@router.patch("/projects/{entity_id}")
def update_project(entity_id: int, payload: dict, session: SessionDep):
    return update_entity(session, Project, entity_id, payload)


@router.delete("/projects/{entity_id}")
def delete_project(entity_id: int, session: SessionDep):
    delete_entity(session, Project, entity_id)
    return {"ok": True}


@router.get("/certifications")
def list_certifications(session: SessionDep):
    profile = _get_profile(session)
    return list_entities(session, Certification, profile.id)


@router.post("/certifications")
def create_certification(payload: CertificationBase, session: SessionDep):
    profile = _get_profile(session)
    return create_entity(session, Certification, payload.model_dump(), profile.id)


@router.patch("/certifications/{entity_id}")
def update_certification(entity_id: int, payload: dict, session: SessionDep):
    return update_entity(session, Certification, entity_id, payload)


@router.delete("/certifications/{entity_id}")
def delete_certification(entity_id: int, session: SessionDep):
    delete_entity(session, Certification, entity_id)
    return {"ok": True}


@router.get("/achievements")
def list_achievements(session: SessionDep):
    profile = _get_profile(session)
    return list_entities(session, Achievement, profile.id)


@router.post("/achievements")
def create_achievement(payload: AchievementBase, session: SessionDep):
    profile = _get_profile(session)
    return create_entity(session, Achievement, payload.model_dump(), profile.id)


@router.patch("/achievements/{entity_id}")
def update_achievement(entity_id: int, payload: dict, session: SessionDep):
    return update_entity(session, Achievement, entity_id, payload)


@router.delete("/achievements/{entity_id}")
def delete_achievement(entity_id: int, session: SessionDep):
    delete_entity(session, Achievement, entity_id)
    return {"ok": True}


@router.get("/preferences")
def get_preferences(session: SessionDep):
    profile = _get_profile(session)
    return profile.preferences


@router.put("/preferences")
def upsert_preferences(payload: CareerPreferenceBase, session: SessionDep):
    profile = _get_profile(session)
    existing = profile.preferences
    from app.models.profile import CareerPreference

    if existing is None:
        existing = CareerPreference(profile_id=profile.id)
        session.add(existing)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(existing, key, value)
    session.commit()
    session.refresh(existing)
    return existing


@router.get("/writing-style")
def get_writing_style(session: SessionDep):
    profile = _get_profile(session)
    return profile.writing_style


@router.put("/writing-style")
def upsert_writing_style(payload: WritingStyleBase, session: SessionDep):
    profile = _get_profile(session)
    existing = profile.writing_style
    if existing is None:
        existing = WritingStyleProfile(profile_id=profile.id)
        session.add(existing)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(existing, key, value)
    session.commit()
    session.refresh(existing)
    return existing


# --------------------------------------------------------------------------- CV import
@router.post("/cv-import", response_model=CVImportResult)
async def import_cv(file: UploadFile = File(...)):
    allowed = (".pdf", ".docx", ".txt", ".md")
    if not file.filename or not file.filename.lower().endswith(allowed):
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Upload a PDF, DOCX, or TXT file.",
        )
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File is too large (max 8 MB).")
    try:
        text = extract_cv_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    extracted, uncertain = extract_cv_structured(text)
    return CVImportResult(
        extracted=extracted,
        uncertain_fields=uncertain,
        warnings=["Imported fields require your confirmation before use."],
    )


@router.post("/cv-import/confirm")
def confirm_cv_import(payload: CVImportConfirmRequest, session: SessionDep):
    """Apply user-approved imported fields to the profile."""
    profile = _get_profile(session)
    approved = payload.approved
    applied: dict[str, Any] = {}

    if approved.get("full_name") and "full_name" in approved:
        profile.full_name = approved["full_name"]
        applied["full_name"] = True
    if approved.get("email"):
        profile.email = approved["email"]
        applied["email"] = True
    if approved.get("phone"):
        profile.phone = approved["phone"]
        applied["phone"] = True
    if approved.get("summary"):
        profile.summary = approved["summary"]
        applied["summary"] = True

    for skill_name in (approved.get("skills") or [])[:30]:
        existing = (
            session.query(Skill)
            .filter(Skill.profile_id == profile.id, Skill.name.ilike(str(skill_name)))
            .first()
        )
        if existing is None:
            session.add(
                Skill(
                    profile_id=profile.id,
                    name=str(skill_name)[:120],
                    category="Imported",
                    verification_status="imported_pending",
                    provenance="cv_import",
                )
            )
    applied["skills"] = len(approved.get("skills") or [])

    session.commit()
    return {"ok": True, "applied": applied}
