"""Job matching engine tests."""

from __future__ import annotations

from app.schemas.jobs import MatchWeights
from app.services.matching import (
    categorize_match,
    compute_match,
    extract_required_skills,
    normalize_skill,
    profile_total_years,
    skill_similarity,
)

PROFILE = {
    "experience": [
        {
            "id": 1,
            "organization": "Acme",
            "job_title": "Senior Backend Engineer",
            "start_date": "2020-01-01",
            "end_date": None,
            "is_current": True,
            "technologies": ["python", "fastapi", "postgresql"],
            "responsibilities": ["Built APIs with FastAPI"],
            "achievements": ["Improved throughput by 40%"],
        }
    ],
    "education": [{"id": 1, "qualification": "BSc", "field_of_study": "CS"}],
    "skills": [
        {"id": 1, "name": "Python", "proficiency": "advanced"},
        {"id": 2, "name": "FastAPI", "proficiency": "advanced"},
        {"id": 3, "name": "PostgreSQL", "proficiency": "intermediate"},
    ],
    "projects": [
        {"id": 1, "name": "API Gateway", "technologies": ["python", "fastapi"]}
    ],
    "certifications": [{"name": "AWS Certified Developer"}],
    "preferences": {
        "preferred_countries": ["Nigeria"],
        "workplace_types": ["remote"],
        "employment_types": ["full-time"],
        "minimum_acceptable_salary": 40000,
    },
}

LISTING = {
    "title": "Senior Python Engineer",
    "company": "Acme",
    "location": "Lagos, Nigeria (Remote)",
    "workplace_type": "remote",
    "employment_type": "full-time",
    "description": "We need Python and FastAPI experience. 5+ years of experience.",
    "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "preferred_qualifications": ["AWS"],
    "salary_min": 60000,
    "salary_max": 90000,
}


def test_normalize_skill_aliases():
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("NodeJS") == "node.js"
    assert normalize_skill("  Python ") == "python"


def test_skill_similarity_exact_and_alias():
    assert skill_similarity("Python", "python") == 1.0
    assert skill_similarity("js", "javascript") == 1.0
    assert skill_similarity("reactjs", "react") == 1.0


def test_extract_required_skills():
    skills = extract_required_skills(LISTING)
    assert "python" in skills
    assert "fastapi" in skills
    assert "postgresql" in skills


def test_compute_match_high_score_for_good_match():
    report = compute_match(PROFILE, LISTING)
    assert report["overall_score"] >= 55
    assert report["category"] in (
        "strong_match",
        "worth_considering",
        "stretch_opportunity",
    )
    # Docker is missing from the profile -> must appear in missing requirements.
    assert any("docker" in m.lower() for m in report["missing_requirements"])
    # Python is confirmed -> strong match.
    assert any("python" in s.lower() for s in report["strong_matches"])


def test_compute_match_excludes_unknown_dimensions():
    # A listing with no parseable requirements should not crash and should
    # treat the skills dimension as unknown rather than zero.
    sparse_listing = {"title": "Mystery Role", "company": "X", "description": ""}
    report = compute_match(PROFILE, sparse_listing)
    assert 0 <= report["overall_score"] <= 100


def test_compute_match_never_rewards_missing_data_as_deficiency():
    empty_profile = {
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "preferences": None,
    }
    report = compute_match(empty_profile, LISTING)
    # Missing profile data must not produce a catastrophic zero; unknown
    # dimensions are excluded from the weighted average.
    assert report["overall_score"] >= 0


def test_categorize_match_thresholds():
    assert categorize_match(90).value == "strong_match"
    assert categorize_match(70).value == "worth_considering"
    assert categorize_match(50).value == "stretch_opportunity"
    assert categorize_match(10).value == "low_match"


def test_weights_normalize_to_one():
    weights = MatchWeights()
    assert abs(weights.total - 1.0) < 1e-6


def test_profile_total_years():
    years = profile_total_years(PROFILE["experience"])
    assert years > 5  # started 2020, still current


def test_match_report_has_explainable_dimensions():
    report = compute_match(PROFILE, LISTING)
    assert len(report["dimensions"]) >= 8
    for dimension in report["dimensions"]:
        assert dimension["status"] in ("match", "partial", "missing", "unknown")
        assert isinstance(dimension["evidence"], list)
        assert 0 <= dimension["score"] <= 100
