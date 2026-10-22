"""Application Studio API - the multi-agent workflow endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.jobs import JobListing
from app.schemas.documents import DocumentCreate, DocumentOut, ReviewRoundsConfig
from app.services.agents.orchestrator import ApplicationWorkflow
from app.services.ai.adapters import get_provider_adapter
from app.services.ai_providers_helpers import get_default_adapter_config
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/api/v1/studio", dependencies=[TokenDep])


@router.post("/generate")
def generate_application(
    payload: DocumentCreate,
    session: SessionDep,
):
    listing = session.get(JobListing, payload.job_listing_id) if payload.job_listing_id else None
    if listing is None:
        raise HTTPException(status_code=404, detail="Job listing not found")

    profile = get_or_create_profile(session)

    config = get_default_adapter_config(session)
    adapter = get_provider_adapter(config) if config else None

    settings_row = session.query(_settings_model()).first()
    rounds = 2
    if settings_row is not None:
        rounds = int((settings_row.settings or {}).get("review_rounds") or 2)

    workflow = ApplicationWorkflow(session, adapter=adapter, rounds=rounds)
    result = workflow.run(
        listing,
        kind=payload.kind,
        template_id=payload.template_id,
        cover_letter_length=payload.cover_letter_length or "standard",
    )
    return result


def _settings_model():
    from app.models.ai import AppSetting

    return AppSetting
