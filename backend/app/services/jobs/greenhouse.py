"""Greenhouse-hosted job boards adapter.

Greenhouse publishes a public JSON API for every company board at
``https://boards-api.greenhouse.io/v1/boards/{token}/jobs``.  It
requires no API key and is documented at
https://developers.greenhouse.io/job-board.html.

Availability is verified at runtime; the adapter reports its own
health and never claims listings it could not retrieve.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.core.security import sanitize_error
from app.services.jobs.base import JobSourceAdapter, SearchQuery, SearchResult

logger = logging.getLogger("careerpilot.jobs.greenhouse")

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseAdapter(JobSourceAdapter):
    name = "greenhouse"
    requires_api_key = False
    supports_search = True

    def __init__(self, company_token: str):
        self.company_token = company_token

    def health_check(self) -> dict:
        try:
            response = httpx.get(
                f"{BASE_URL}/{quote(self.company_token)}/jobs",
                params={"per_page": 1},
                timeout=10.0,
            )
            if response.status_code == 200:
                return {"available": True, "company": self.company_token}
            return {"available": False, "error": f"HTTP {response.status_code}"}
        except Exception as exc:
            return {"available": False, "error": sanitize_error(exc)}

    def search(self, query: SearchQuery) -> SearchResult:
        try:
            response = httpx.get(
                f"{BASE_URL}/{quote(self.company_token)}/jobs",
                params={"per_page": 100},
                timeout=15.0,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            return SearchResult(
                source_name="greenhouse",
                errors=[f"Greenhouse board request failed: {sanitize_error(exc)}"],
            )

        listings = []
        for job in payload.get("jobs", []):
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            if query.title and query.title.lower() not in title.lower():
                continue
            if query.keywords:
                text = f"{title} {job.get('content', '')}".lower()
                if not any(k.lower() in text for k in query.keywords.split()):
                    continue
            listings.append(
                {
                    "external_id": str(job.get("id", "")),
                    "title": title,
                    "company": payload.get("name", self.company_token),
                    "location": location,
                    "workplace_type": "remote" if "remote" in location.lower() else None,
                    "description": self._job_description(job),
                    "url": job.get("absolute_url"),
                    "application_url": job.get("absolute_url"),
                    "publication_date": job.get("updated_at"),
                }
            )
            if query.limit and len(listings) >= query.limit:
                break

        return SearchResult(
            listings=listings, total=len(listings), source_name="greenhouse"
        )

    def _job_description(self, job: dict) -> str | None:
        content = job.get("content", "")
        if content:
            return content[:8000]
        return None

    def import_url(self, url: str) -> dict | None:
        return None
