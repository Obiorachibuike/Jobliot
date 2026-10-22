"""Job source registry.

Sources are instantiated from persisted JobSource records so new
providers can be added without touching the discovery service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.jobs.base import JobSourceAdapter, SearchQuery, SearchResult
from app.services.jobs.greenhouse import GreenhouseAdapter
from app.services.jobs.lever import LeverAdapter
from app.services.jobs.manual import ManualEntryAdapter
from app.services.jobs.url_import import UrlImportAdapter

if TYPE_CHECKING:
    from app.models.jobs import JobSource

ADAPTER_CLASSES: dict[str, type[JobSourceAdapter]] = {
    "manual": ManualEntryAdapter,
    "url_import": UrlImportAdapter,
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
}

# Capabilities advertised to the UI.
SOURCE_CAPABILITIES = {
    "manual": {"search": False, "url_import": False, "requires_key": False},
    "url_import": {"search": False, "url_import": True, "requires_key": False},
    "greenhouse": {"search": True, "url_import": False, "requires_key": False},
    "lever": {"search": True, "url_import": False, "requires_key": False},
}


def build_adapter(source: JobSource) -> JobSourceAdapter | None:
    source_type = source.source_type
    adapter_class = ADAPTER_CLASSES.get(source_type)
    if adapter_class is None:
        return None
    config = source.config or {}
    if source_type == "greenhouse":
        return GreenhouseAdapter(company_token=config.get("company_token", ""))
    if source_type == "lever":
        return LeverAdapter(company=config.get("company", ""))
    return adapter_class()


def available_source_types() -> dict[str, dict]:
    return dict(SOURCE_CAPABILITIES)
