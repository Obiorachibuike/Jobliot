"""Agent 4: Revision.

Applies reviewer findings to improve the draft while preserving
factual accuracy.  Anything that would require inventing facts
is escalated to the user rather than silently changed.
"""

from __future__ import annotations

import json

from app.services.agents.base import AgentBase, AgentContext
from app.services.agents.local_engine import local_revise

SYSTEM_PROMPT = """You are a Document Reviser. Given a draft document and reviewer findings,
produce an improved document. Rules:
- Preserve factual accuracy; never add achievements, employers, skills, metrics, or dates
  that are not in the verified profile.
- Fix grammar, repetition, filler, length, and keyword placement issues.
- Findings marked requires_user_confirmation must NOT be auto-fixed; list them as unresolved.
Output ONLY a JSON object:
{"content": <document object>, "changes": [str], "findings_addressed": [str],
 "findings_unresolved": [{"id": str, "message": str}], "status": str}"""


class ReviserAgent(AgentBase):
    stage_name = "revision"

    def run(self, context: AgentContext) -> dict:
        if self.adapter is not None:
            payload = {
                "document": context.document,
                "findings": context.findings,
                "verified_facts": context.profile.get("skills") or [],
            }
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)[:14000]},
            ]
            result = self._ai_complete_json(messages, task="revision")
            if result and isinstance(result.get("content"), dict):
                result.setdefault("changes", [])
                result.setdefault("findings_addressed", [])
                result.setdefault("findings_unresolved", [])
                result["source"] = "ai"
                return result

        result = local_revise(context.document or {}, context.findings or [], context.profile, context.listing)
        result["source"] = "local"
        return result
