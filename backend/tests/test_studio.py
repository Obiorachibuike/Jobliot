"""Application Studio: multi-agent workflow tests."""

from __future__ import annotations

from app.services.agents.local_engine import (
    local_draft_cover_letter,
    local_draft_cv,
    local_review,
    local_revise,
    local_strategy,
)
from app.services.matching import compute_match

PROFILE = {
    "full_name": "Ada Okafor",
    "preferred_name": "Ada",
    "headline": "Backend Engineer",
    "email": "ada@example.com",
    "location_city": "Lagos",
    "location_country": "Nigeria",
    "experience": [
        {
            "id": 1,
            "organization": "Acme",
            "job_title": "Backend Engineer",
            "start_date": "2021-01-01",
            "end_date": None,
            "is_current": True,
            "technologies": ["python", "fastapi"],
            "responsibilities": ["Built REST APIs"],
            "achievements": ["Cut response times by 40%"],
        }
    ],
    "education": [{"id": 1, "institution": "UNILAG", "qualification": "BSc", "field_of_study": "CS"}],
    "skills": [
        {"id": 1, "name": "Python", "proficiency": "advanced"},
        {"id": 2, "name": "FastAPI", "proficiency": "advanced"},
        {"id": 3, "name": "Docker", "proficiency": "intermediate"},
    ],
    "projects": [{"id": 1, "name": "API Gateway", "technologies": ["python", "fastapi"], "is_public": True}],
    "certifications": [],
    "writing_style": {"uses_first_person": True, "disliked_phrases": []},
}

LISTING = {
    "title": "Senior Python Engineer",
    "company": "Acme",
    "description": "Needs Python, FastAPI, Docker.",
    "requirements": ["Python", "FastAPI", "Docker"],
}


def test_strategist_selects_relevant_evidence():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    assert strategy["positioning"]
    assert strategy["selected_experience"]
    assert strategy["selected_skills"]
    assert "key_messages" in strategy


def test_drafter_produces_structured_cv():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    cv = local_draft_cv(PROFILE, strategy, LISTING, "ats_friendly")
    assert cv["sections"]
    section_ids = {s["id"] for s in cv["sections"]}
    assert "summary" in section_ids
    assert "experience" in section_ids
    # The CV must not invent employers or titles.
    text = str(cv)
    assert "Acme" in text
    assert "Ada Okafor" in text


def test_drafter_produces_cover_letter():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    letter = local_draft_cover_letter(PROFILE, strategy, LISTING, "standard")
    assert letter["sections"]
    body = str(letter)
    assert "Senior Python Engineer" in body


def test_reviewer_finds_missing_keywords():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    cv = local_draft_cv(PROFILE, strategy, LISTING, "ats_friendly")
    review = local_review(cv, LISTING, PROFILE, report)
    assert review["findings"] is not None
    assert "readiness" in review
    # All findings must carry severity and category.
    for finding in review["findings"]:
        assert finding["severity"] in ("critical", "major", "minor", "suggestion")
        assert finding["category"]


def test_reviewer_flags_unverified_claims():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    cv = local_draft_cv(PROFILE, strategy, LISTING, "ats_friendly")
    # Inject a fabricated technology claim (Kubernetes is a
    # real technology but is NOT in the verified profile).
    cv["sections"][0]["blocks"][0]["text"] += " Expert in Kubernetes."
    review = local_review(cv, LISTING, PROFILE, report)
    critical = [f for f in review["findings"] if f["severity"] == "critical"]
    assert critical, "Fabricated claims must be flagged as critical"


def test_reviser_fixes_deterministic_issues():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    cv = local_draft_cv(PROFILE, strategy, LISTING, "ats_friendly")
    # Add a double-space and a repeated bullet.
    cv["sections"][0]["blocks"][0]["text"] = "Experienced  engineer."
    cv["sections"][1]["blocks"][0]["items"] = ["Built APIs", "Built APIs"]
    review = local_review(cv, LISTING, PROFILE, report)
    revision = local_revise(cv, review["findings"], PROFILE, LISTING)
    assert revision["changes"]
    # Double space should be collapsed.
    assert "  " not in revision["content"]["sections"][0]["blocks"][0]["text"]
    # Duplicate bullet removed.
    items = revision["content"]["sections"][1]["blocks"][0]["items"]
    assert items.count("Built APIs") == 1


def test_reviser_escalates_fabrications():
    report = compute_match(PROFILE, LISTING)
    strategy = local_strategy(PROFILE, LISTING, report)
    cv = local_draft_cv(PROFILE, strategy, LISTING, "ats_friendly")
    cv["sections"][0]["blocks"][0]["text"] += " Expert in Kubernetes."
    review = local_review(cv, LISTING, PROFILE, report)
    revision = local_revise(cv, review["findings"], PROFILE, LISTING)
    unresolved_ids = [f.get("id") for f in revision["findings_unresolved"]]
    assert any(str(i).startswith("fab-") for i in unresolved_ids)


def test_quality_gate_blocks_approval_with_critical_findings(client, auth_headers):
    from app.models.documents import Document, DocumentStatus
    from app.core.database import get_session_factory

    session = get_session_factory()()
    document = Document(
        profile_id=1,
        kind="cv",
        title="Gated CV",
        content={"sections": []},
        status=DocumentStatus.READY_FOR_APPROVAL.value,
        meta={"final_review": {"critical_count": 2}},
    )
    session.add(document)
    session.commit()
    document_id = document.id
    session.close()

    response = client.post(
        f"/api/v1/documents/{document_id}/approve", headers=auth_headers
    )
    assert response.status_code == 409
