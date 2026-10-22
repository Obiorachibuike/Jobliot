"""Job discovery, URL import, and suitability matching API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.jobs import JobListing, JobMatch, JobSearch, JobSource
from app.schemas.jobs import (
    JobListingFilters,
    JobListingOut,
    JobSourceCreate,
    JobSourceOut,
    JobUrlImportRequest,
    JobUrlImportResult,
    ManualJobCreate,
    MatchReportOut,
    MatchWeights,
    SavedSearchBase,
    SavedSearchOut,
)
from app.services import jobs_service
from app.services.matching import compute_match
from app.services.profile_service import get_or_create_profile
from app.services.settings_service import get_match_weights

router = APIRouter(prefix="/api/v1/jobs", dependencies=[TokenDep])


def _listing_out(listing: JobListing, session: Session | None = None) -> dict:
    match = None
    if session is not None:
        match = (
            session.query(JobMatch)
            .filter(JobMatch.job_listing_id == listing.id)
            .order_by(JobMatch.id.desc())
            .first()
        )
    return {
        **{
            column: getattr(listing, column)
            for column in JobListing.__table__.columns.keys()
        },
        "has_match": match is not None,
        "match_score": match.overall_score if match else None,
        "match_category": match.category if match else None,
    }


# --------------------------------------------------------------------------- sources
@router.get("/sources", response_model=list[JobSourceOut])
def list_sources(session: SessionDep):
    return session.query(JobSource).order_by(JobSource.id).all()


@router.post("/sources", response_model=JobSourceOut)
def create_source(payload: JobSourceCreate, session: SessionDep):
    from app.services.jobs import registry

    capabilities = registry.SOURCE_CAPABILITIES.get(payload.source_type)
    if capabilities is None:
        raise HTTPException(status_code=400, detail=f"Unknown source type: {payload.source_type}")
    source = JobSource(
        name=payload.name,
        source_type=payload.source_type,
        config=payload.config or {},
        enabled=payload.enabled,
        requires_api_key=capabilities["requires_key"],
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, session: SessionDep):
    source = session.get(JobSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    session.delete(source)
    session.commit()
    return {"ok": True}


@router.get("/sources/available")
def available_source_types():
    from app.services.jobs import registry

    return registry.available_source_types()


@router.post("/sources/{source_id}/health")
def check_source_health(source_id: int, session: SessionDep):
    source = session.get(JobSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    from app.services.jobs import registry as job_registry

    adapter = job_registry.build_adapter(source)
    if adapter is None:
        raise HTTPException(status_code=400, detail="Unsupported source type")
    return adapter.health_check()


@router.post("/discover")
def discover(payload: JobListingFilters | None = None, session: SessionDep = None):
    from app.services.jobs.base import SearchQuery

    filters = payload.model_dump(exclude_none=True) if payload else {}
    query = SearchQuery(
        title=filters.get("title"),
        keywords=filters.get("keywords"),
        country=filters.get("country"),
        city=filters.get("city"),
        workplace_type=filters.get("workplace_type"),
        employment_type=filters.get("employment_type"),
        experience_level=filters.get("experience_level"),
        salary_min=filters.get("salary_min"),
        salary_max=filters.get("salary_max"),
        technology=filters.get("technology"),
        limit=filters.get("limit", 25) or 25,
    )
    result = jobs_service.discover_from_sources(session, query)
    return result


# --------------------------------------------------------------------------- saved searches
# NOTE: static routes must be registered BEFORE the /{listing_id} dynamic
# routes, otherwise "searches" would be captured as a listing id.

@router.get("/searches", response_model=list[SavedSearchOut])
def list_searches(session: SessionDep):
    return session.query(JobSearch).order_by(JobSearch.id.desc()).all()


@router.post("/searches", response_model=SavedSearchOut)
def create_search(payload: SavedSearchBase, session: SessionDep):
    search = JobSearch(**payload.model_dump())
    session.add(search)
    session.commit()
    session.refresh(search)
    return search


@router.delete("/searches/{search_id}")
def delete_search(search_id: int, session: SessionDep):
    search = session.get(JobSearch, search_id)
    if search is None:
        raise HTTPException(status_code=404, detail="Saved search not found")
    session.delete(search)
    session.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- listings
@router.get("", response_model=list[JobListingOut])
def list_listings(
    session: SessionDep,
    q: str | None = Query(default=None),
    title: str | None = None,
    company: str | None = None,
    location: str | None = None,
    workplace_type: str | None = None,
    employment_type: str | None = None,
    source: str | None = None,
    min_match_score: float | None = None,
    limit: int = 100,
    offset: int = 0,
):
    filters = {
        "q": q,
        "title": title,
        "company": company,
        "location": location,
        "workplace_type": workplace_type,
        "employment_type": employment_type,
        "source": source,
        "min_match_score": min_match_score,
        "limit": min(limit, 200),
        "offset": offset,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    listings = jobs_service.search_listings(session, filters)
    outputs = []
    for listing in listings:
        match = (
            session.query(JobMatch)
            .filter(JobMatch.job_listing_id == listing.id)
            .order_by(JobMatch.id.desc())
            .first()
        )
        if min_match_score is not None:
            if match is None or match.overall_score < min_match_score:
                continue
        outputs.append(_listing_out(listing, session))
    return outputs


@router.post("/manual", response_model=JobListingOut)
def create_manual_job(payload: ManualJobCreate, session: SessionDep):
    listing = jobs_service.create_manual_listing(session, payload.model_dump())
    return _listing_out(listing, session)


@router.post("/import-url", response_model=JobUrlImportResult)
def import_url(payload: JobUrlImportRequest, session: SessionDep):
    result = jobs_service.import_job_url(session, payload.url)
    return JobUrlImportResult(**result)


@router.get("/{listing_id}", response_model=JobListingOut)
def get_listing(listing_id: int, session: SessionDep):
    listing = jobs_service.get_listing(session, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Job listing not found")
    return _listing_out(listing, session)


@router.delete("/{listing_id}")
def delete_listing(listing_id: int, session: SessionDep):
    jobs_service.delete_listing(session, listing_id)
    return {"ok": True}


@router.post("/{listing_id}/verify")
def verify_listing(listing_id: int, session: SessionDep):
    listing = jobs_service.refresh_verification(session, listing_id)
    return {"ok": True, "last_verified": listing.last_verified.isoformat()}


# --------------------------------------------------------------------------- matching
@router.post("/{listing_id}/match", response_model=MatchReportOut)
def compute_listing_match(listing_id: int, session: SessionDep):
    listing = jobs_service.get_listing(session, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Job listing not found")

    profile = get_or_create_profile(session)
    profile_data = _profile_data(session, profile.id)

    weights_data = get_match_weights(session)
    weights = MatchWeights(**{
        k: v for k, v in weights_data.items() if k in MatchWeights.model_fields
    }) if weights_data else MatchWeights()

    listing_dict = {
        column: getattr(listing, column)
        for column in JobListing.__table__.columns.keys()
    }
    report = compute_match(profile_data, listing_dict, weights)
    report["job_listing_id"] = listing.id

    match_record = JobMatch(
        job_listing_id=listing.id,
        overall_score=report["overall_score"],
        category=report["category"],
        dimensions=report["dimensions"],
        strong_matches=report["strong_matches"],
        partial_matches=report["partial_matches"],
        missing_requirements=report["missing_requirements"],
        potential_disqualifiers=report["potential_disqualifiers"],
        unknown_items=report["unknown_items"],
        factors=report["factors"],
        narrative=report["narrative"],
        weights_snapshot=report["weights_snapshot"],
    )
    session.add(match_record)
    session.commit()

    return report


def _profile_data(session: Session, profile_id: int) -> dict:
    profile = get_or_create_profile(session)
    return {
        "experience": [
            {
                "id": e.id,
                "organization": e.organization,
                "job_title": e.job_title,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "is_current": e.is_current,
                "technologies": e.technologies or [],
                "responsibilities": e.responsibilities or [],
                "achievements": e.achievements or [],
                "outcomes": e.outcomes,
            }
            for e in profile.experience
        ],
        "education": [
            {
                "id": e.id,
                "qualification": e.qualification,
                "field_of_study": e.field_of_study,
            }
            for e in profile.education
        ],
        "skills": [
            {"id": s.id, "name": s.name, "proficiency": s.proficiency}
            for s in profile.skills
        ],
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "technologies": p.technologies or [],
                "is_public": p.is_public,
            }
            for p in profile.projects
        ],
        "certifications": [
            {"name": c.name, "issuing_organization": c.issuing_organization}
            for c in profile.certifications
        ],
        "preferences": (
            {
                "preferred_countries": profile.preferences.preferred_countries,
                "preferred_cities": profile.preferences.preferred_cities,
                "workplace_types": profile.preferences.workplace_types,
                "employment_types": profile.preferences.employment_types,
                "minimum_acceptable_salary": profile.preferences.minimum_acceptable_salary,
                "experience_level": profile.preferences.experience_level,
            }
            if profile.preferences
            else None
        ),
    }


# --------------------------------------------------------------------------- saved searches
# (registered above the dynamic /{listing_id} routes on purpose)
