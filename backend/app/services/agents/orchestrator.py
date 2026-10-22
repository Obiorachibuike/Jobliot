"""Application workflow orchestrator.

Runs the four agents as separate, explicit stages:
Strategy -> Draft -> Review -> (Revise -> Review)* -> Approval gate.

Quality gates: a document can never reach ``ready_for_approval``
while critical factual findings are unresolved, and it can never
be auto-approved - the user must approve explicitly.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.documents import Document, DocumentStatus, DocumentVersion
from app.models.profile import UserProfile
from app.services.agents.base import AgentContext
from app.services.agents.drafter import DrafterAgent
from app.services.agents.reviewer import ReviewerAgent
from app.services.agents.reviser import ReviserAgent
from app.services.agents.strategist import StrategistAgent
from app.services.matching import compute_match
from app.schemas.jobs import MatchWeights

logger = logging.getLogger("careerpilot.orchestrator")


def _profile_dict(session: Session) -> dict:
    profile = session.query(UserProfile).first()
    if profile is None:
        return {}
    return {
        "full_name": profile.full_name,
        "preferred_name": profile.preferred_name,
        "headline": profile.headline,
        "summary": profile.summary,
        "email": profile.email,
        "phone": profile.phone,
        "location_city": profile.location_city,
        "location_country": profile.location_country,
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "website": profile.website,
        "portfolio_url": profile.portfolio_url,
        "experience": [
            {
                "id": e.id,
                "organization": e.organization,
                "job_title": e.job_title,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "is_current": e.is_current,
                "responsibilities": e.responsibilities or [],
                "achievements": e.achievements or [],
                "technologies": e.technologies or [],
                "outcomes": e.outcomes,
            }
            for e in profile.experience
        ],
        "education": [
            {
                "id": e.id,
                "institution": e.institution,
                "qualification": e.qualification,
                "field_of_study": e.field_of_study,
                "start_date": str(e.start_date) if e.start_date else None,
                "end_date": str(e.end_date) if e.end_date else None,
                "is_current": e.is_current,
            }
            for e in profile.education
        ],
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "proficiency": s.proficiency,
                "years_experience": s.years_experience,
            }
            for s in profile.skills
        ],
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "problem_solved": p.problem_solved,
                "technologies": p.technologies or [],
                "responsibilities": p.responsibilities or [],
                "outcomes": p.outcomes,
                "repository_url": p.repository_url,
                "live_demo_url": p.live_demo_url,
                "is_public": p.is_public,
            }
            for p in profile.projects
        ],
        "certifications": [
            {"id": c.id, "name": c.name, "issuing_organization": c.issuing_organization}
            for c in profile.certifications
        ],
        "achievements": [
            {"kind": a.kind, "title": a.title, "description": a.description}
            for a in profile.achievements
        ],
        "preferences": _prefs_dict(profile.preferences),
        "writing_style": _style_dict(profile.writing_style),
    }


def _prefs_dict(prefs) -> dict | None:
    if prefs is None:
        return None
    return {
        "preferred_countries": prefs.preferred_countries or [],
        "preferred_cities": prefs.preferred_cities or [],
        "workplace_types": prefs.workplace_types or [],
        "employment_types": prefs.employment_types or [],
        "minimum_acceptable_salary": prefs.minimum_acceptable_salary,
        "experience_level": prefs.experience_level,
    }


def _style_dict(style) -> dict | None:
    if style is None:
        return None
    return {
        "formality": style.formality,
        "detail_level": style.detail_level,
        "confidence_tone": style.confidence_tone,
        "cover_letter_length": style.cover_letter_length,
        "uses_first_person": style.uses_first_person,
        "disliked_phrases": style.disliked_phrases or [],
    }


def _listing_dict(listing) -> dict:
    return {
        "title": listing.title,
        "company": listing.company,
        "location": listing.location,
        "workplace_type": listing.workplace_type,
        "employment_type": listing.employment_type,
        "description": listing.description,
        "requirements": listing.requirements or [],
        "preferred_qualifications": listing.preferred_qualifications or [],
        "salary_min": listing.salary_min,
        "salary_max": listing.salary_max,
    }


class ApplicationWorkflow:
    """Runs the strategy -> draft -> review -> revise pipeline."""

    def __init__(self, session: Session, adapter=None, rounds: int = 2):
        self.session = session
        self.adapter = adapter
        self.rounds = max(1, min(5, rounds or 2))

    def _context(self, listing, kind: str) -> AgentContext:
        profile = _profile_dict(self.session)
        match_report = compute_match(profile, _listing_dict(listing))
        return AgentContext(
            profile=profile,
            listing=_listing_dict(listing),
            match_report=match_report,
        )

    def run(self, listing, kind: str = "cv", template_id: str = "ats_friendly",
            cover_letter_length: str = "standard") -> dict:
        context = self._context(listing, kind)

        # Stage 1: strategy
        strategist = StrategistAgent(self.adapter, self.session)
        strategy = strategist.run(context)
        context.strategy = strategy

        # Stage 2: draft
        drafter = DrafterAgent(self.adapter, self.session)
        document = drafter.run(context, kind=kind, template_id=template_id)
        context.document = document

        # Persist the draft before review so work survives interruptions.
        from app.services.profile_service import get_or_create_profile

        profile_row = get_or_create_profile(self.session)
        db_document = Document(
            profile_id=profile_row.id,
            job_listing_id=getattr(listing, "id", None),
            kind=kind,
            title=document.get("title") or "Application document",
            template_id=template_id,
            status=DocumentStatus.UNDER_REVIEW.value,
            content=document,
            strategy=strategy,
            match_data=context.match_report,
        )
        self.session.add(db_document)
        self.session.flush()  # assign document.id before versioning
        self._save_version(db_document, 1, document, "draft", "Initial draft", [])
        self.session.commit()

        # Stage 3+4: review/revise rounds
        last_review = None
        for round_number in range(1, self.rounds + 1):
            reviewer = ReviewerAgent(self.adapter, self.session)
            review = reviewer.run(context)
            last_review = review
            self.session.flush()
            self._save_version(
                db_document,
                db_document.current_version,
                context.document,
                "review",
                f"Review round {round_number}",
                review.get("findings") or [],
            )

            critical = [f for f in review.get("findings", []) if f.get("severity") == "critical"]
            if not critical:
                break

            reviser = ReviserAgent(self.adapter, self.session)
            context.findings = review.get("findings") or []
            revision = reviser.run(context)
            context.document = revision["content"]
            db_document.content = revision["content"]
            db_document.current_version += 1
            self.session.flush()
            self._save_version(
                db_document,
                db_document.current_version,
                revision["content"],
                "revision",
                f"Revision round {round_number}: "
                + "; ".join(c.get("action", "") for c in revision.get("changes", [])[:5]),
                revision.get("findings_unresolved") or [],
            )
            self.session.commit()

        # Final gate. The reviewer's readiness verdict drives
        # the document status so the two never disagree.
        final_review = last_review or {}
        unresolved_critical = [
            f for f in final_review.get("findings", [])
            if f.get("severity") == "critical" and not f.get("resolved")
        ]
        requires_confirmation = bool(
            unresolved_critical
            or any(f.get("requires_user_confirmation") for f in final_review.get("findings", []))
        )
        readiness = final_review.get("readiness", "needs_confirmation")
        if unresolved_critical or readiness == "not_ready":
            status = DocumentStatus.NEEDS_USER_CONFIRMATION
        elif requires_confirmation or readiness == "needs_confirmation":
            status = DocumentStatus.NEEDS_USER_CONFIRMATION
        else:
            status = DocumentStatus.READY_FOR_APPROVAL

        db_document.status = status.value
        db_document.meta = {
            "review_rounds": self.rounds,
            "final_review": final_review,
            "agent_source": document.get("source", "local"),
        }
        self.session.commit()
        self.session.refresh(db_document)

        return {
            "document_id": db_document.id,
            "document": _document_out(db_document),
            "strategy": strategy,
            "review": final_review,
            "status": db_document.status,
            "readiness": readiness,
        }

    def _save_version(self, document: Document, number: int, content: dict,
                      stage: str, summary: str, findings: list) -> None:
        version = DocumentVersion(
            document_id=document.id,
            version_number=number,
            content=content,
            status=document.status,
            change_summary=summary,
            agent_stage=stage,
            findings=findings or [],
        )
        self.session.add(version)


def _document_out(document: Document) -> dict:
    return {
        "id": document.id,
        "kind": document.kind,
        "title": document.title,
        "template_id": document.template_id,
        "status": document.status,
        "content": document.content,
        "strategy": document.strategy,
        "match_data": document.match_data,
        "current_version": document.current_version,
        "approved_by_user": document.approved_by_user,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
    }
