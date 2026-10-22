"""Agent 1: Career Strategist.

Produces a structured application plan: positioning, selected
verified evidence, key messages, gaps, and keyword targets.
"""

from __future__ import annotations

import json

from app.services.agents.base import AgentBase, AgentContext, profile_public_summary
from app.services.agents.local_engine import local_strategy

SYSTEM_PROMPT = """You are a Career Strategist for a privacy-conscious job-search assistant.
Your job: analyze a job description against the user's VERIFIED career profile and
produce an application strategy. You must never invent experience, skills, employers,
metrics, or credentials. If information is missing, say so. Output ONLY a JSON object
matching this schema:
{
  "positioning": "one sentence positioning statement",
  "selected_experience": [{"id": int, "organization": str, "job_title": str}],
  "selected_projects": [{"id": int, "name": str}],
  "selected_skills": [str],
  "key_messages": [str, str, str],
  "gaps": [str],
  "gap_mitigations": [str],
  "keyword_targets": [str],
  "evidence_refs": []
}"""


class StrategistAgent(AgentBase):
    stage_name = "strategy"

    def run(self, context: AgentContext) -> dict:
        if self.adapter is not None:
            payload = {
                "job": {
                    "title": context.listing.get("title"),
                    "company": context.listing.get("company"),
                    "requirements": context.listing.get("requirements") or [],
                    "description": (context.listing.get("description") or "")[:3000],
                },
                "profile": profile_public_summary(context.profile),
            }
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ]
            result = self._ai_complete_json(messages, task="strategy")
            if result and isinstance(result, dict) and result.get("positioning"):
                result["source"] = "ai"
                return result

        result = local_strategy(context.profile, context.listing, context.match_report or {})
        result["source"] = "local"
        return result
