"""Onboarding and career-profile persistence tests."""

from __future__ import annotations


def _profile_id(client, headers):
    return client.get("/api/v1/profile", headers=headers).json()["id"]


def test_onboarding_state_starts_empty(client, auth_headers):
    response = client.get("/api/v1/onboarding/state", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["onboarding_completed"] is False
    assert body["profile_exists"] is True


def test_onboarding_step_persists(client, auth_headers):
    response = client.post(
        "/api/v1/onboarding/step",
        headers=auth_headers,
        json={"step": 1, "data": {"objectives": ["Find a full-time job"]}},
    )
    assert response.status_code == 200
    assert response.json()["objectives"] == ["Find a full-time job"]

    response = client.post(
        "/api/v1/onboarding/step",
        headers=auth_headers,
        json={
            "step": 2,
            "data": {
                "full_name": "Ada Okafor",
                "headline": "Backend Engineer",
                "location_city": "Lagos",
                "location_country": "Nigeria",
            },
        },
    )
    assert response.status_code == 200

    profile = client.get("/api/v1/profile", headers=auth_headers).json()
    assert profile["full_name"] == "Ada Okafor"
    assert profile["headline"] == "Backend Engineer"


def test_onboarding_complete_flag(client, auth_headers):
    response = client.post(
        "/api/v1/onboarding/complete", headers=auth_headers, json={}
    )
    assert response.status_code == 200
    state = client.get("/api/v1/onboarding/state", headers=auth_headers).json()
    assert state["onboarding_completed"] is True


def test_experience_crud(client, auth_headers):
    payload = {
        "organization": "Acme Corp",
        "job_title": "Software Engineer",
        "employment_type": "full-time",
        "responsibilities": ["Built APIs", "Wrote tests"],
        "achievements": ["Reduced latency by 40%"],
        "technologies": ["Python", "FastAPI"],
    }
    response = client.post("/api/v1/experience", headers=auth_headers, json=payload)
    assert response.status_code == 200
    entity_id = response.json()["id"]

    response = client.get("/api/v1/experience", headers=auth_headers)
    assert len(response.json()) == 1

    response = client.patch(
        f"/api/v1/experience/{entity_id}",
        headers=auth_headers,
        json={"job_title": "Senior Software Engineer"},
    )
    assert response.json()["job_title"] == "Senior Software Engineer"

    response = client.delete(f"/api/v1/experience/{entity_id}", headers=auth_headers)
    assert response.status_code == 200
    assert client.get("/api/v1/experience", headers=auth_headers).json() == []


def test_skills_crud_with_verification_status(client, auth_headers):
    payload = {
        "name": "Python",
        "category": "Programming languages",
        "proficiency": "advanced",
        "years_experience": 5,
        "verification_status": "user_confirmed",
    }
    response = client.post("/api/v1/skills", headers=auth_headers, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "user_confirmed"
    assert body["provenance"] == "user"


def test_education_and_projects_crud(client, auth_headers):
    edu = {
        "institution": "University of Lagos",
        "qualification": "BSc",
        "field_of_study": "Computer Science",
    }
    assert client.post("/api/v1/education", headers=auth_headers, json=edu).status_code == 200

    project = {
        "name": "Jobliot Parser",
        "technologies": ["Python", "BeautifulSoup"],
        "is_public": True,
    }
    assert client.post("/api/v1/projects", headers=auth_headers, json=project).status_code == 200

    assert len(client.get("/api/v1/education", headers=auth_headers).json()) == 1
    assert len(client.get("/api/v1/projects", headers=auth_headers).json()) == 1


def test_preferences_and_writing_style(client, auth_headers):
    prefs = {
        "desired_job_titles": ["Backend Engineer"],
        "preferred_countries": ["Nigeria", "Remote"],
        "workplace_types": ["remote", "hybrid"],
        "minimum_acceptable_salary": 50000,
        "currency": "USD",
    }
    response = client.put("/api/v1/preferences", headers=auth_headers, json=prefs)
    assert response.status_code == 200
    assert response.json()["desired_job_titles"] == ["Backend Engineer"]

    style = {"formality": "balanced", "detail_level": "standard", "uses_first_person": True}
    response = client.put("/api/v1/writing-style", headers=auth_headers, json=style)
    assert response.status_code == 200


def test_full_profile_snapshot(client, auth_headers):
    # After adding data, the profile endpoint still returns the base profile.
    client.post(
        "/api/v1/onboarding/step",
        headers=auth_headers,
        json={"step": 2, "data": {"full_name": "Test User"}},
    )
    profile = client.get("/api/v1/profile", headers=auth_headers).json()
    assert profile["full_name"] == "Test User"
