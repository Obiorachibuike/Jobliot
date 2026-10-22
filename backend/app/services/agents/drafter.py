"""Agent 2: Document Drafter.

Drafts CV and cover letter from the approved strategy.
The drafter is forbidden from inventing facts: it works
from the verified profile and strategy selections only.
"""

from __future__ import annotations

import json

from app.services.agents.base import AgentBase, AgentContext, profile_public_summary
from app.services.agents.local_engine import local_draft_cover_letter, local_draft_cv

SYSTEM_PROMPT = """You are a Document Drafter. Given a verified career profile, a job
description, and an approved strategy, draft a tailored CV or cover letter.
Rules:
- NEVER invent employers, job titles, degrees, certifications, skills, dates, metrics, or outcomes.
- Use only facts present in the profile.
- Match the user's writing style preferences.
- Output ONLY a JSON object: {"title": str, "subtitle": str|null, "contact_line": str|null,
  "sections": [{"id": str, "heading": str, "blocks": [{"type": "paragraph"|"bullets"|"entry", ...}]}]}"""


class DrafterAgent(AgentBase):
    stage_name = "draft"

    def run(self, context: AgentContext, kind: str = "cv", template_id: str = "ats_friendly") -> dict:
        if self.adapter is not None:
            payload = {
                "kind": kind,
                "template_id": template_id,
                "job": {
                    "title": context.listing.get("title"),
                    "company": context.listing.get("company"),
                    "requirements": context.listing.get("requirements") or [],
                },
                "profile": profile_public_summary(context.profile),
                "strategy": context.strategy,
                "cover_letter_length": context.options.get("cover_letter_length", "standard"),
            }
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ]
            result = self._ai_complete_json(messages, task="draft")
            if result and isinstance(result.get("sections"), list):
                result.setdefault("title", "Draft")
                result.setdefault("template_id", template_id)
                result["source"] = "ai"
                return result

        if kind == "cover_letter":
            length = context.options.get("cover_letter_length", "standard")
            document = local_draft_cover_letter(context.profile, context.strategy or {}, context.listing, length)
        else:
            document = local_draft_cv(context.profile, context.strategy or {}, context.listing, template_id)
        document["source"] = "local"
        return document
