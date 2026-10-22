"""Job source adapter interface and registry.

Every job source implements the same capability interface.
Providers that need credentials report ``requires_api_key``
so the UI can surface configuration requirements honestly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchQuery:
    title: str | None = None
    keywords: str | None = None
    country: str | None = None
    city: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technology: str | None = None
    limit: int = 25


@dataclass
class SearchResult:
    listings: list[dict] = field(default_factory=list)
    total: int = 0
    source_name: str = ""
    errors: list[str] = field(default_factory=list)
    partial: bool = False


class JobSourceAdapter(ABC):
    """Contract every job source must satisfy."""

    name: str = "base"
    requires_api_key: bool = False
    supports_search: bool = False

    @abstractmethod
    def health_check(self) -> dict:
        """Return availability info without mutating state."""

    @abstractmethod
    def search(self, query: SearchQuery) -> SearchResult:
        """Search listings, if the source supports search."""

    @abstractmethod
    def import_url(self, url: str) -> dict | None:
        """Import a specific job URL, if supported."""
