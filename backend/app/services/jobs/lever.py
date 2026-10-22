"""Lever-hosted job boards adapter.

Lever publishes public posting feeds at
``https://api.lever.co/v0/postings/{company}?mode=json``.
No API key is required for public boards.  Availability is
verified at runtime.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

from app.core.security import sanitize_error
from app.services.jobs.base import JobSourceAdapter, SearchQuery, SearchResult

logger = logging.getLogger("careerpilot.jobs.lever")

BASE_URL = "https://api.lever.co/v0/postings"


class LeverAdapter(JobSourceAdapter):
    name = "lever"
    requires_api_key = False
    supports_search = True

    def __init__(self, company: str):
        self.company = company

    def health_check(self) -> dict:
        try:
            response = httpx.get(
                f"{BASE_URL}/{quote(self.company)}",
                params={"mode": "json", "limit": 1},
                timeout=10.0,
            )
            if response.status_code == 200:
                return {"available": True, "company": self.company}
            return {"available": False, "error": f"HTTP {response.status_code}"}
        except Exception as exc:
            return {"available": False, "error": sanitize_error(exc)}

    def search(self, query: SearchQuery) -> SearchResult:
        try:
            response = httpx.get(
                f"{BASE_URL}/{quote(self.company)}",
                params={"mode": "json", "limit": 100},
                timeout=15.0,
            )
            response.raise_for_status()
            postings = response.json()
        except Exception as exc:
            return SearchResult(
                source_name="lever",
                errors=[f"Lever board request failed: {sanitize_error(exc)}"],
            )

        listings = []
        for posting in postings:
            title = posting.get("text", "")
            categories = posting.get("categories") or {}
            location = posting.get("locations") or []
            location_str = ", ".join(
                loc.get("description", "") for loc in location
            ) if location else (categories.get("location") or "")
            workplace = categories.get("workplace") or None
            if query.title and query.title.lower() not in title.lower():
                continue
            listings.append(
                {
                    "external_id": posting.get("id", ""),
                    "title": title,
                    "company": posting.get("company", self.company),
                    "location": location_str or None,
                    "workplace_type": workplace,
                    "description": posting.get("description", {}).get("content")
                    if isinstance(posting.get("description"), dict)
                    else None,
                    "url": posting.get("hostedUrl"),
                    "application_url": posting.get("applyUrl"),
                    "publication_date": posting.get("createdAt"),
                }
            )
            if query.limit and len(listings) >= query.limit:
                break

        return SearchResult(
            listings=listings, total=len(listings), source_name="lever"
        )

    def import_url(self, url: str) -> dict | None:
        return None
