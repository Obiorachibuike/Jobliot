"""Application tracker, interviews, insights, privacy tests."""

from __future__ import annotations

import base64
import json


def _create_application(client, headers, **overrides):
    payload = {
        "company": "Acme",
        "job_title": "Backend Engineer",
        "location": "Lagos",
        "source_name": "manual",
        "status": "saved",
    }
    payload.update(overrides)
    response = client.post("/api/v1/applications", headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()


def test_application_create_and_status_flow(client, auth_headers):
    application = _create_application(client, auth_headers)
    app_id = application["id"]

    response = client.post(
        f"/api/v1/applications/{app_id}/status",
        headers=auth_headers,
        json={"status": "applied"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "applied"

    events = client.get(
        f"/api/v1/applications/{app_id}/events", headers=auth_headers
    ).json()
    assert any(e["event_type"] == "status_change" for e in events)


def test_application_invalid_status_rejected(client, auth_headers):
    application = _create_application(client, auth_headers)
    response = client.post(
        f"/api/v1/applications/{application['id']}/status",
        headers=auth_headers,
        json={"status": "hired-tomorrow"},
    )
    assert response.status_code == 400


def test_application_filter_by_status(client, auth_headers):
    _create_application(client, auth_headers, status="applied")
    _create_application(client, auth_headers, status="rejected")
    response = client.get(
        "/api/v1/applications", headers=auth_headers, params={"status": "applied"}
    )
    assert all(a["status"] == "applied" for a in response.json())


def test_application_analytics_computed_from_data(client, auth_headers):
    _create_application(client, auth_headers, status="interview", source_name="greenhouse")
    _create_application(client, auth_headers, status="applied", source_name="greenhouse")
    _create_application(client, auth_headers, status="saved", source_name="manual")

    response = client.get("/api/v1/applications/analytics", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_applications"] == 3
    assert body["by_status"]["interview"] == 1
    assert "response_rate" in body


def test_reminder_crud(client, auth_headers):
    application = _create_application(client, auth_headers)
    payload = {
        "application_id": application["id"],
        "kind": "followup",
        "title": "Follow up with recruiter",
        "due_at": "2026-11-01T10:00:00",
    }
    response = client.post("/api/v1/applications/reminders", headers=auth_headers, json=payload)
    assert response.status_code == 200
    reminder_id = response.json()["id"]

    response = client.patch(
        f"/api/v1/applications/reminders/{reminder_id}",
        headers=auth_headers,
        json={"is_done": True},
    )
    assert response.json()["is_done"] is True


def test_interview_session_generation_and_evaluation(client, auth_headers):
    session_response = client.post(
        "/api/v1/interviews/sessions",
        headers=auth_headers,
        json={"title": "Prep for Acme"},
    )
    assert session_response.status_code == 200
    session_data = session_response.json()
    session_id = session_data["id"]
    assert len(session_data["questions"]) >= 5

    question_id = session_data["questions"][0]["id"]
    answer_response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answer/{question_id}",
        headers=auth_headers,
        json={
            "answer_text": "In my previous role at Acme, I faced a situation where the API was slow. "
            "My task was to diagnose it. I profiled the endpoints and found an N+1 query. "
            "I added caching, which reduced latency by 60%.",
            "duration_seconds": 90,
        },
    )
    assert answer_response.status_code == 200
    scores = answer_response.json()["scores"]
    assert "overall" in scores
    assert "relevance" in scores


def test_insights_reflect_real_data(client, auth_headers):
    # Add a job with requirements, then match it.
    listing = client.post(
        "/api/v1/jobs/manual",
        headers=auth_headers,
        json={
            "title": "Python Engineer",
            "company": "InsightCo",
            "requirements": ["Python", "Django", "Redis"],
        },
    ).json()
    client.post(f"/api/v1/jobs/{listing['id']}/match", headers=auth_headers)

    response = client.get("/api/v1/insights", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["job_listings"] >= 1
    assert "insights" in body


def test_insight_dismissal_persists(client, auth_headers):
    response = client.post(
        "/api/v1/insights/skill-demand/dismiss", headers=auth_headers
    )
    assert response.status_code == 200
    dismissed = client.get("/api/v1/insights/dismissed", headers=auth_headers).json()
    assert "skill-demand" in dismissed["dismissed"]


def test_data_export_contains_profile(client, auth_headers):
    client.post(
        "/api/v1/onboarding/step",
        headers=auth_headers,
        json={"step": 2, "data": {"full_name": "Export Test"}},
    )
    response = client.get("/api/v1/privacy/export", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    raw = base64.b64decode(body["content_b64"])
    data = json.loads(raw)
    assert data["profile"][0]["full_name"] == "Export Test"
    # Secrets must never be exported.
    assert "api_token" not in raw.decode()
    assert "api_key" not in raw.decode()


def test_backup_and_integrity(client, auth_headers):
    response = client.post("/api/v1/privacy/backup", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["size_bytes"] > 0

    integrity = client.get("/api/v1/privacy/integrity", headers=auth_headers)
    assert integrity.json()["ok"] is True


def test_delete_documents_scope(client, auth_headers):
    from app.models.documents import Document, DocumentStatus
    from app.core.database import get_session_factory

    session = get_session_factory()()
    document = Document(profile_id=1, kind="cv", title="ToDelete", content={})
    session.add(document)
    session.commit()
    document_id = document.id
    session.close()

    response = client.post(
        "/api/v1/privacy/delete",
        headers=auth_headers,
        json={"scope": "documents", "document_ids": [document_id], "confirm": True},
    )
    assert response.json()["deleted"] == 1


def test_delete_requires_confirmation(client, auth_headers):
    response = client.post(
        "/api/v1/privacy/delete",
        headers=auth_headers,
        json={"scope": "documents", "document_ids": [1], "confirm": False},
    )
    assert response.status_code == 400
