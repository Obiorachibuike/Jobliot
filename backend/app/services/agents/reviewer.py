"""Agent 3: Independent Reviewer.

Evaluates a draft independently against the job description
and verified profile.  Returns structured findings with
severity, location, evidence, and recommended corrections.
The reviewer never approves a document without examining it.
"""

from __future__ import annotations

import json

from app.services.agents.base import AgentBase, AgentContext
from app.services.agents.local_engine import doc_text, local_review

SYSTEM_PROMPT = """You are an Independent Application Reviewer. You review a draft CV or
cover letter against the job description and the user's VERIFIED profile.
Evaluate: factual accuracy, unsupported claims, job relevance, required skills,
ATS readability, keyword relevance, professional tone, grammar, clarity,
conciseness, style consistency, repetition, missing evidence, misleading wording.
Output ONLY a JSON object:
{"findings": [{"id": str, "severity": "critical|major|minor|suggestion",
"category": str, "location": str|null, "message": str, "evidence": str|null,
"recommendation": str|null, "requires_user_confirmation": bool, "resolved": false}],
"overall_assessment": str}
Be skeptical. If a claim cannot be traced to the verified profile, it is a critical finding.
Do NOT simply approve: list at least the checks you performed."""


class ReviewerAgent(AgentBase):
    stage_name = "review"

    def run(self, context: AgentContext) -> dict:
        if self.adapter is not None:
            payload = {
                "document": context.document,
                "job": {
                    "title": context.listing.get("title"),
                    "requirements": context.listing.get("requirements") or [],
                },
                "verified_facts": profile_fact_list(context),
            }
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)[:12000]},
            ]
            result = self._ai_complete_json(messages, task="review")
            if result and isinstance(result.get("findings"), list):
                result.setdefault("overall_assessment", "AI review completed.")
                counts = _count(result["findings"])
                result.update(counts)
                result["readiness"] = _readiness(counts)
                result["source"] = "ai"
                return result

        result = local_review(context.document or {}, context.listing, context.profile, context.match_report or {})
        result["source"] = "local"
        return result


def profile_fact_list(context: AgentContext) -> list[str]:
    facts = []
    for exp in context.profile.get("experience") or []:
        facts.append(f"{exp.get('job_title')} at {exp.get('organization')}")
    for skill in context.profile.get("skills") or []:
        facts.append(f"skill: {skill.get('name')} ({skill.get('proficiency')})")
    for project in context.profile.get("projects") or []:
        facts.append(f"project: {project.get('name')}")
    for cert in context.profile.get("certifications") or []:
        facts.append(f"certification: {cert.get('name')}")
    for edu in context.profile.get("education") or []:
        facts.append(f"education: {edu.get('qualification')} at {edu.get('institution')}")
    return facts


def _count(findings: list[dict]) -> dict:
    counts = {"critical_count": 0, "major_count": 0, "minor_count": 0, "suggestion_count": 0}
    for finding in findings:
        severity = finding.get("severity")
        key = f"{severity}_count"
        if key in counts:
            counts[key] += 1
    return counts


def _readiness(counts: dict) -> str:
    if counts["critical_count"] > 0:
        return "not_ready"
    if counts["major_count"] > 0:
        return "needs_confirmation"
    return "ready"
