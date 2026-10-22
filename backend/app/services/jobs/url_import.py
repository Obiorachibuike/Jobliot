"""Job URL import with SSRF-safe fetching and structured extraction.

Retrieved pages are treated as untrusted data: they are parsed for
facts, never executed, and never allowed to influence application
behavior.  JSON-LD ``JobPosting`` markup is used when present.
"""

from __future__ import annotations

import json
import logging
import re
from html import unescape

from bs4 import BeautifulSoup

from app.core.security import safe_fetch, sanitize_error
from app.services.jobs.base import JobSourceAdapter, SearchQuery, SearchResult

logger = logging.getLogger("careerpilot.jobs.url_import")


class UrlImportAdapter(JobSourceAdapter):
    name = "url_import"
    requires_api_key = False
    supports_search = False

    def health_check(self) -> dict:
        return {"available": True, "note": "URL import available for public job pages"}

    def search(self, query: SearchQuery) -> SearchResult:
        return SearchResult(
            listings=[], source_name="url_import",
            errors=["URL import retrieves specific pages; it does not search."],
        )

    def import_url(self, url: str) -> dict | None:
        try:
            response = safe_fetch(url)
        except Exception as exc:
            return {
                "ok": False,
                "error": sanitize_error(exc),
                "extracted": None,
            }

        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            data = response.json()
            return {"ok": True, "extracted": _extract_from_json_ld(data)}

        html = response.text
        return {"ok": True, "extracted": _extract_from_html(html, url)}


def _extract_from_json_ld(data) -> dict:
    """Extract from JSON-LD JobPosting structures (many boards embed them)."""
    candidates = []
    if isinstance(data, dict):
        if data.get("@type") == "JobPosting":
            candidates.append(data)
        for value in data.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        candidates.append(item)
                    elif isinstance(item, dict):
                        nested = _extract_from_json_ld(item)
                        if nested:
                            candidates.append(nested)
    if not candidates:
        return {}

    posting = candidates[0]
    title = posting.get("title")
    company = None
    hiring_org = posting.get("hiringOrganization") or {}
    if isinstance(hiring_org, dict):
        company = hiring_org.get("name")
    job_location = posting.get("jobLocation") or {}
    location = None
    if isinstance(job_location, dict):
        address = job_location.get("address") or {}
        if isinstance(address, dict):
            location = ", ".join(
                str(address.get(k)) for k in ("addressLocality", "addressRegion", "addressCountry") if address.get(k)
            )
    description = posting.get("description") or ""
    employment_type = posting.get("employmentType")
    if isinstance(employment_type, list):
        employment_type = ", ".join(employment_type)
    salary = posting.get("baseSalary") or {}
    salary_min = salary_max = None
    if isinstance(salary, dict):
        value = salary.get("value") or {}
        if isinstance(value, dict):
            salary_min = value.get("minValue")
            salary_max = value.get("maxValue")

    requirements = []
    for prop in ("qualifications", "skills", "responsibilities"):
        value = posting.get(prop)
        if isinstance(value, str):
            requirements.extend([s.strip() for s in re.split(r"[.\n]", value) if s.strip()][:10])

    return {
        "title": title,
        "company": company,
        "location": location,
        "description": _clean_text(description),
        "requirements": requirements,
        "employment_type": employment_type,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "extraction_method": "json-ld",
    }


def _extract_from_html(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Check for embedded JSON-LD first.
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        extracted = _extract_from_json_ld(payload)
        if extracted.get("title"):
            return extracted

    title = None
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = og_title["content"]
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()

    description = ""
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        description = og_desc["content"]
    if not description:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]

    # Heuristic: the largest text block is usually the description.
    if len(description) < 200:
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        candidates = []
        for element in soup.find_all(["div", "section", "article", "main"]):
            text = element.get_text(" ", strip=True)
            if 300 < len(text) < 20000:
                candidates.append(text)
        if candidates:
            description = max(candidates, key=len)

    company = _guess_company(url, title or "")

    return {
        "title": title,
        "company": company,
        "location": None,
        "description": _clean_text(description),
        "requirements": [],
        "employment_type": None,
        "salary_min": None,
        "salary_max": None,
        "extraction_method": "html-heuristic",
        "needs_review": True,
    }


def _guess_company(url: str, title: str) -> str | None:
    match = re.search(r"https?://(?:www\.)?([^/\.]+)\.", url)
    if match:
        name = match.group(1).replace("-", " ").replace("_", " ")
        return name.title()
    return None


def _clean_text(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
