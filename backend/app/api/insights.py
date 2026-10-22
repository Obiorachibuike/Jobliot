"""Career insights API - computed from real stored data only."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.applications import Application, InterviewSession, UserFeedback
from app.models.documents import DocumentVersion
from app.models.jobs import JobListing, JobMatch
from app.services.matching import extract_required_skills

router = APIRouter(prefix="/api/v1/insights", dependencies=[TokenDep])


@router.get("")
def career_insights(session: SessionDep):
    listings = session.query(JobListing).all()
    matches = session.query(JobMatch).all()
    applications = session.query(Application).all()
    review_findings = session.query(DocumentVersion).filter(
        DocumentVersion.agent_stage == "review"
    ).all()

    insights = []

    # 1. Most frequently requested skills.
    skill_demand: Counter = Counter()
    for listing in listings:
        for skill in extract_required_skills(
            {
                "title": listing.title,
                "description": listing.description,
                "requirements": listing.requirements or [],
            }
        )[:8]:
            skill_demand[skill] += 1
    if skill_demand:
        top = skill_demand.most_common(6)
        insights.append(
            {
                "id": "skill-demand",
                "title": "Most frequently requested skills",
                "description": "Across your saved listings, these skills appear most often: "
                + ", ".join(f"{name} ({count})" for name, count in top)
                + ".",
                "kind": "trend",
                "metric": f"{len(top)} skills",
                "evidence": {"skills": top},
                "how_calculated": "Keyword extraction from saved job requirements, counted per listing.",
            }
        )

    # 2. Common missing qualifications.
    missing_counter: Counter = Counter()
    for match in matches:
        for item in match.missing_requirements or []:
            missing_counter[item] += 1
    if missing_counter:
        top_missing = missing_counter.most_common(5)
        insights.append(
            {
                "id": "common-gaps",
                "title": "Common missing qualifications",
                "description": "Your match reports most often lack: "
                + ", ".join(f"{name} ({count} job(s))" for name, count in top_missing)
                + ". These are gaps in evidence, not proof you lack the skill.",
                "kind": "gap",
                "metric": f"{len(top_missing)} gaps",
                "evidence": {"gaps": top_missing},
                "how_calculated": "Aggregated missing-requirement lists from match reports.",
                "dismissable": True,
            }
        )

    # 3. Strongest-match industries/companies.
    strong = [m for m in matches if m.overall_score >= 75]
    if strong:
        companies = Counter(
            session.get(JobListing, m.job_listing_id).company
            for m in strong
            if session.get(JobListing, m.job_listing_id)
        )
        top_companies = companies.most_common(3)
        insights.append(
            {
                "id": "strong-match-companies",
                "title": "Companies with the strongest matches",
                "description": "Your highest-scoring matches cluster at: "
                + ", ".join(f"{name} ({count})" for name, count in top_companies)
                + ".",
                "kind": "strength",
                "metric": f"{len(strong)} strong matches",
                "evidence": {"companies": top_companies},
                "how_calculated": "Companies of listings whose match score is >= 75.",
            }
        )

    # 4. Source effectiveness.
    source_interviews: Counter = Counter()
    source_applied: Counter = Counter()
    for application in applications:
        source = application.source_name or "manual"
        if application.status in ("applied", "assessment", "interview", "offer"):
            source_applied[source] += 1
        if application.status in ("interview", "offer"):
            source_interviews[source] += 1
    if source_applied:
        rates = [
            (source, round(100 * source_interviews.get(source, 0) / count, 1))
            for source, count in source_applied.items()
        ]
        rates.sort(key=lambda pair: -pair[1])
        insights.append(
            {
                "id": "source-effectiveness",
                "title": "Application sources producing interviews",
                "description": "Interview conversion by source: "
                + ", ".join(f"{source} {rate}%" for source, rate in rates[:4])
                + ". Correlation is not causation - sample sizes may be small.",
                "kind": "source",
                "metric": f"{len(rates)} sources",
                "evidence": {"rates": rates},
                "how_calculated": "Interviews divided by applications reaching 'applied' or beyond, grouped by source.",
            }
        )

    # 5. Recurring review findings.
    finding_counter: Counter = Counter()
    for version in review_findings:
        for finding in version.findings or []:
            if isinstance(finding, dict):
                finding_counter[finding.get("category", "other")] += 1
    if finding_counter:
        top_issues = finding_counter.most_common(4)
        insights.append(
            {
                "id": "review-themes",
                "title": "Recurring document review themes",
                "description": "The reviewer most often flags: "
                + ", ".join(f"{name} ({count}x)" for name, count in top_issues)
                + ".",
                "kind": "review",
                "metric": f"{len(top_issues)} themes",
                "evidence": {"themes": top_issues},
                "how_calculated": "Finding categories aggregated across saved review rounds.",
            }
        )

    # 6. Job titles generating the most relevant opportunities.
    if matches:
        title_scores: dict[str, list[float]] = {}
        for match in matches:
            listing = session.get(JobListing, match.job_listing_id)
            if listing is None:
                continue
            title_scores.setdefault(listing.title, []).append(match.overall_score)
        averages = [
            (title, round(sum(scores) / len(scores), 1))
            for title, scores in title_scores.items()
        ]
        averages.sort(key=lambda pair: -pair[1])
        best = averages[:3]
        insights.append(
            {
                "id": "title-fit",
                "title": "Job titles with the best average fit",
                "description": "Highest average match scores: "
                + ", ".join(f"{title} ({score})" for title, score in best)
                + ".",
                "kind": "trend",
                "metric": f"{len(averages)} titles",
                "evidence": {"averages": best},
                "how_calculated": "Mean match score per job title across all matches.",
            }
        )

    stats = {
        "job_listings": len(listings),
        "match_reports": len(matches),
        "applications": len(applications),
        "strong_matches": len(strong),
        "interview_sessions": session.query(InterviewSession).count(),
        "review_rounds_saved": len(review_findings),
    }

    return {"generated_at": datetime.utcnow().isoformat(), "insights": insights, "stats": stats}


@router.post("/{insight_id}/dismiss")
def dismiss_insight(insight_id: str, session: SessionDep):
    existing = (
        session.query(UserFeedback)
        .filter(UserFeedback.kind == "insight_dismissed")
        .first()
    )
    content = dict(existing.content) if existing else {}
    dismissed = list(content.get("dismissed") or [])
    if insight_id not in dismissed:
        dismissed.append(insight_id)
    if existing is None:
        existing = UserFeedback(kind="insight_dismissed", content={"dismissed": dismissed})
        session.add(existing)
    else:
        existing.content = {"dismissed": dismissed}
    session.commit()
    return {"ok": True, "dismissed": dismissed}


@router.get("/dismissed")
def dismissed_insights(session: SessionDep):
    record = (
        session.query(UserFeedback)
        .filter(UserFeedback.kind == "insight_dismissed")
        .first()
    )
    if record is None:
        return {"dismissed": []}
    return {"dismissed": (record.content or {}).get("dismissed", [])}
