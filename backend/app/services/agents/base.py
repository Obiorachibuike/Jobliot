"""Shared agent plumbing: AI dispatch, usage recording, fallbacks."""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.services.ai.adapters import get_provider_adapter, parse_json_response
from app.services.ai.base import estimate_cost
from app.models.ai import AIUsageRecord

logger = logging.getLogger("careerpilot.agents")


class AgentContext:
    """Everything an agent is allowed to see for one task.

    Deliberately narrow: agents receive the job listing, the
    verified profile summary, and stage-specific inputs - never
    the raw secrets, settings, or unrelated history.
    """

    def __init__(
        self,
        profile: dict,
        listing: dict,
        match_report: dict | None = None,
        strategy: dict | None = None,
        document: dict | None = None,
        findings: list | None = None,
        options: dict | None = None,
    ):
        self.profile = profile
        self.listing = listing
        self.match_report = match_report
        self.strategy = strategy
        self.document = document
        self.findings = findings
        self.options = options or {}


def profile_public_summary(profile: dict) -> dict:
    """Trim the profile to what drafting legitimately needs."""
    return {
        "full_name": profile.get("full_name"),
        "preferred_name": profile.get("preferred_name"),
        "headline": profile.get("headline"),
        "summary": profile.get("summary"),
        "location": f"{profile.get('location_city') or ''}, {profile.get('location_country') or ''}".strip(", "),
        "experience": [
            {
                "organization": e.get("organization"),
                "job_title": e.get("job_title"),
                "start_date": str(e.get("start_date") or ""),
                "end_date": str(e.get("end_date") or "") if not e.get("is_current") else None,
                "is_current": e.get("is_current"),
                "technologies": e.get("technologies") or [],
                "responsibilities": (e.get("responsibilities") or [])[:6],
                "achievements": (e.get("achievements") or [])[:6],
                "outcomes": e.get("outcomes"),
            }
            for e in (profile.get("experience") or [])
        ],
        "education": [
            {
                "institution": e.get("institution"),
                "qualification": e.get("qualification"),
                "field_of_study": e.get("field_of_study"),
            }
            for e in (profile.get("education") or [])
        ],
        "skills": [
            {"name": s.get("name"), "category": s.get("category"), "proficiency": s.get("proficiency")}
            for s in (profile.get("skills") or [])
        ],
        "projects": [
            {
                "name": p.get("name"),
                "description": p.get("description"),
                "technologies": p.get("technologies") or [],
                "outcomes": p.get("outcomes"),
            }
            for p in (profile.get("projects") or [])
        ],
        "certifications": [
            {"name": c.get("name"), "issuing_organization": c.get("issuing_organization")}
            for c in (profile.get("certifications") or [])
        ],
        "writing_style": profile.get("writing_style"),
    }


class AgentBase:
    stage_name = "agent"

    def __init__(self, adapter=None, usage_session: Session | None = None):
        self.adapter = adapter
        self.usage_session = usage_session

    def _record_usage(self, task: str, result, status: str = "ok", error: str | None = None, duration_ms: int = 0) -> None:
        if self.usage_session is None:
            return
        try:
            record = AIUsageRecord(
                provider=getattr(result, "provider", None) or (self.adapter.name if self.adapter else None),
                model=getattr(result, "model", None) or (self.adapter.model if self.adapter else None),
                task=task,
                prompt_tokens=getattr(result, "prompt_tokens", None),
                completion_tokens=getattr(result, "completion_tokens", None),
                total_tokens=getattr(result, "total_tokens", None),
                estimated_cost=estimate_cost(
                    getattr(result, "model", "") or "",
                    getattr(result, "prompt_tokens", 0) or 0,
                    getattr(result, "completion_tokens", 0) or 0,
                ) if getattr(result, "prompt_tokens", None) else None,
                duration_ms=duration_ms,
                status=status,
                error=error[:400] if error else None,
            )
            self.usage_session.add(record)
            self.usage_session.commit()
        except Exception as exc:  # pragma: no cover
            logger.warning("Could not record AI usage: %s", exc)
            self.usage_session.rollback()

    def _ai_complete_json(self, messages: list[dict], task: str) -> dict | None:
        """Call the provider and parse JSON.  Returns None on failure."""
        if self.adapter is None:
            return None
        started = time.monotonic()
        try:
            result = self.adapter.complete_with_retry(messages, task=task)
        except Exception as exc:
            self._record_usage(task, None, status="error", error=str(exc)[:400], duration_ms=int((time.monotonic() - started) * 1000))
            logger.warning("AI call failed for %s: %s", task, exc)
            return None
        self._record_usage(task, result, duration_ms=result.latency_ms)
        try:
            return parse_json_response(result.text)
        except Exception as exc:
            logger.warning("AI returned unparseable JSON for %s: %s", task, exc)
            return None

    def run(self, context: AgentContext) -> dict:
        raise NotImplementedError
