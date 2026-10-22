"""Job discovery service: search, import, dedup, persistence."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.jobs import JobListing, JobSource, ListingStatus
from app.services.jobs import registry
from app.services.jobs.base import SearchQuery
from app.services.matching import extract_required_skills

logger = logging.getLogger("careerpilot.jobs")


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    cleaned = url.strip().split("#")[0]
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


def compute_dedup_hash(listing: dict) -> str:
    """Stable hash over the fields that identify the same opportunity."""
    title = re.sub(r"\W+", "", (listing.get("title") or "").lower())
    company = re.sub(r"\W+", "", (listing.get("company") or "").lower())
    location = re.sub(r"\W+", "", (listing.get("location") or "").lower())
    url = normalize_url(listing.get("url") or listing.get("application_url")) or ""
    # Description fingerprint: first 200 normalized words.
    words = re.findall(r"[a-z0-9]+", (listing.get("description") or "").lower())[:200]
    desc_fp = " ".join(words)
    payload = f"{title}|{company}|{location}|{url}|{desc_fp}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def find_duplicate(session: Session, dedup_hash: str) -> JobListing | None:
    if not dedup_hash:
        return None
    return (
        session.query(JobListing)
        .filter(JobListing.dedup_hash == dedup_hash)
        .order_by(JobListing.date_discovered.desc())
        .first()
    )


def upsert_listing(session: Session, data: dict, source_name: str | None = None) -> JobListing:
    """Insert a listing or return the existing record (dedup)."""
    dedup_hash = compute_dedup_hash(data)
    existing = find_duplicate(session, dedup_hash)
    if existing is not None:
        return existing

    listing = JobListing(
        source_name=source_name,
        title=data.get("title") or "Untitled position",
        company=data.get("company") or "Unknown company",
        location=data.get("location"),
        workplace_type=data.get("workplace_type"),
        employment_type=data.get("employment_type"),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        salary_currency=data.get("salary_currency"),
        description=data.get("description"),
        requirements=data.get("requirements") or [],
        preferred_qualifications=data.get("preferred_qualifications") or [],
        publication_date=data.get("publication_date"),
        closing_date=data.get("closing_date"),
        url=normalize_url(data.get("url")),
        application_url=normalize_url(data.get("application_url")),
        external_id=str(data.get("external_id") or ""),
        dedup_hash=dedup_hash,
        raw_data=data.get("raw_data"),
    )
    session.add(listing)
    session.commit()
    session.refresh(listing)
    return listing


def get_listing(session: Session, listing_id: int) -> JobListing | None:
    return session.get(JobListing, listing_id)


def search_listings(session: Session, filters: dict) -> list[JobListing]:
    query = session.query(JobListing)

    q = filters.get("q")
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            (JobListing.title.ilike(pattern))
            | (JobListing.company.ilike(pattern))
            | (JobListing.description.ilike(pattern))
            | (JobListing.location.ilike(pattern))
        )
    if filters.get("title"):
        query = query.filter(JobListing.title.ilike(f"%{filters['title']}%"))
    if filters.get("company"):
        query = query.filter(JobListing.company.ilike(f"%{filters['company']}%"))
    if filters.get("location"):
        query = query.filter(JobListing.location.ilike(f"%{filters['location']}%"))
    if filters.get("city"):
        query = query.filter(JobListing.location.ilike(f"%{filters['city']}%"))
    if filters.get("country"):
        query = query.filter(JobListing.location.ilike(f"%{filters['country']}%"))
    if filters.get("workplace_type"):
        query = query.filter(JobListing.workplace_type == filters["workplace_type"])
    if filters.get("employment_type"):
        query = query.filter(JobListing.employment_type == filters["employment_type"])
    if filters.get("source"):
        query = query.filter(JobListing.source_name == filters["source"])
    if filters.get("salary_min") is not None:
        query = query.filter(
            (JobListing.salary_max.is_(None))
            | (JobListing.salary_max >= filters["salary_min"])
        )
    if filters.get("published_since_days") is not None:
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=filters["published_since_days"])
        query = query.filter(JobListing.date_discovered >= cutoff)

    return (
        query.order_by(JobListing.date_discovered.desc())
        .offset(filters.get("offset", 0))
        .limit(filters.get("limit", 100))
        .all()
    )


def create_manual_listing(session: Session, data: dict) -> JobListing:
    listing_data = dict(data)
    listing_data.setdefault("source_name", "manual")
    listing_data.pop("id", None)
    return upsert_listing(session, listing_data, source_name="manual")


def import_job_url(session: Session, url: str) -> dict:
    adapter = registry.UrlImportAdapter()
    result = adapter.import_url(url)
    if result is None or not result.get("ok"):
        return {
            "ok": False,
            "error": (result or {}).get("error", "The URL could not be imported."),
            "extracted": None,
        }
    extracted = result.get("extracted") or {}
    if not extracted.get("title"):
        return {
            "ok": False,
            "error": (
                "No job title could be extracted from this page. "
                "Paste the job description manually instead."
            ),
            "extracted": extracted,
            "partial": True,
        }
    extracted.setdefault("url", url)
    extracted.setdefault("application_url", url)
    listing = upsert_listing(session, extracted, source_name="url_import")
    return {"ok": True, "listing_id": listing.id, "extracted": extracted}


def run_source_search(session: Session, source: JobSource, query: SearchQuery) -> SearchResult:
    adapter = registry.build_adapter(source)
    if adapter is None:
        return SearchResult(
            source_name=source.name,
            errors=[f"Unknown source type: {source.source_type}"],
        )
    source.health_status = "checking"
    session.commit()
    try:
        result = adapter.search(query)
        source.health_status = "ok"
        source.last_checked = datetime.utcnow()
        source.error_message = None
    except Exception as exc:
        source.health_status = "error"
        source.error_message = str(exc)[:400]
        result = SearchResult(source_name=source.name, errors=[str(exc)[:400]])
    session.commit()
    return result


def discover_from_sources(session: Session, query: SearchQuery, source_ids: list[int] | None = None) -> dict:
    """Run a search across enabled sources, dedup, persist."""
    sources_query = session.query(JobSource).filter(JobSource.enabled.is_(True))
    if source_ids:
        sources_query = sources_query.filter(JobSource.id.in_(source_ids))
    sources = sources_query.all()

    all_listings: list[JobListing] = []
    errors: list[str] = []
    for source in sources:
        if source.source_type == "manual":
            continue
        result = run_source_search(session, source, query)
        if result.errors:
            errors.extend(result.errors)
        for item in result.listings:
            item.setdefault("raw_data", {"source": source.name})
            listing = upsert_listing(session, item, source_name=source.name)
            all_listings.append(listing)

    return {
        "discovered": len(all_listings),
        "new": len(all_listings),
        "errors": errors,
        "listing_ids": [l.id for l in all_listings],
    }


def delete_listing(session: Session, listing_id: int) -> bool:
    listing = session.get(JobListing, listing_id)
    if listing is None:
        raise LookupError("Job listing not found")
    session.delete(listing)
    session.commit()
    return True


def refresh_verification(session: Session, listing_id: int) -> JobListing:
    """Mark a listing as re-verified (called after URL checks)."""
    listing = session.get(JobListing, listing_id)
    if listing is None:
        raise LookupError("Job listing not found")
    listing.last_verified = datetime.utcnow()
    listing.status = ListingStatus.ACTIVE.value
    session.commit()
    session.refresh(listing)
    return listing
