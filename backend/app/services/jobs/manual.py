"""Manual job entry adapter - always available, no credentials."""

from __future__ import annotations

from app.services.jobs.base import JobSourceAdapter, SearchQuery, SearchResult


class ManualEntryAdapter(JobSourceAdapter):
    name = "manual"
    requires_api_key = False
    supports_search = False

    def health_check(self) -> dict:
        return {"available": True, "note": "Manual entry always available"}

    def search(self, query: SearchQuery) -> SearchResult:
        return SearchResult(
            listings=[], source_name="manual",
            errors=["Manual entry does not support search; add jobs individually."],
        )

    def import_url(self, url: str) -> dict | None:
        return None
