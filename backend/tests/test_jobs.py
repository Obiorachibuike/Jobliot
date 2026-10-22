"""Job discovery, URL import, and deduplication tests."""

from __future__ import annotations


def test_manual_job_entry(client, auth_headers):
    payload = {
        "title": "Python Developer",
        "company": "TestCo",
        "location": "Lagos",
        "workplace_type": "remote",
        "employment_type": "full-time",
        "description": "Build APIs with Python and FastAPI.",
        "requirements": ["Python", "FastAPI"],
        "application_url": "https://testco.example/apply",
    }
    response = client.post("/api/v1/jobs/manual", headers=auth_headers, json=payload)
    assert response.status_code == 200
    listing_id = response.json()["id"]
    assert response.json()["title"] == "Python Developer"

    listings = client.get("/api/v1/jobs", headers=auth_headers).json()
    assert any(item["id"] == listing_id for item in listings)


def test_deduplication_prevents_duplicates(client, auth_headers):
    payload = {
        "title": "Data Engineer",
        "company": "DupCo",
        "description": "Work with Python and Spark.",
        "requirements": ["Python", "Spark"],
    }
    first = client.post("/api/v1/jobs/manual", headers=auth_headers, json=payload)
    second = client.post("/api/v1/jobs/manual", headers=auth_headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    listings = client.get("/api/v1/jobs", headers=auth_headers).json()
    titles = [item["title"] for item in listings]
    assert titles.count("Data Engineer") == 1


def test_job_filters(client, auth_headers):
    for title in ["Frontend React Developer", "Backend Python Developer"]:
        client.post(
            "/api/v1/jobs/manual",
            headers=auth_headers,
            json={"title": title, "company": "FilterCo", "description": title},
        )
    response = client.get(
        "/api/v1/jobs", headers=auth_headers, params={"q": "python"}
    )
    titles = [item["title"] for item in response.json()]
    assert all("Python" in t for t in titles)


def test_url_import_rejects_private_host(client, auth_headers):
    response = client.post(
        "/api/v1/jobs/import-url",
        headers=auth_headers,
        json={"url": "http://169.254.169.254/latest/meta-data"},
    )
    body = response.json()
    assert body["ok"] is False
    assert body["error"]


def test_url_import_rejects_non_http_scheme(client, auth_headers):
    response = client.post(
        "/api/v1/jobs/import-url",
        headers=auth_headers,
        json={"url": "file:///etc/passwd"},
    )
    assert response.json()["ok"] is False


def test_match_endpoint_produces_report(client, auth_headers):
    listing = client.post(
        "/api/v1/jobs/manual",
        headers=auth_headers,
        json={
            "title": "Senior Python Engineer",
            "company": "MatchCo",
            "description": "Needs Python, FastAPI, Docker.",
            "requirements": ["Python", "FastAPI", "Docker"],
        },
    ).json()

    response = client.post(
        f"/api/v1/jobs/{listing['id']}/match", headers=auth_headers
    )
    assert response.status_code == 200
    report = response.json()
    assert "overall_score" in report
    assert "dimensions" in report
    assert "category" in report
    assert "missing_requirements" in report


def test_match_report_persists_and_listing_shows_score(client, auth_headers):
    listing = client.post(
        "/api/v1/jobs/manual",
        headers=auth_headers,
        json={
            "title": "DevOps Engineer",
            "company": "InfraCo",
            "requirements": ["Docker", "Kubernetes"],
        },
    ).json()
    client.post(f"/api/v1/jobs/{listing['id']}/match", headers=auth_headers)

    listings = client.get("/api/v1/jobs", headers=auth_headers).json()
    target = next(item for item in listings if item["id"] == listing["id"])
    assert target["has_match"] is True
    assert target["match_score"] is not None


def test_source_registry_and_health(client, auth_headers):
    response = client.get("/api/v1/jobs/sources/available", headers=auth_headers)
    assert response.status_code == 200
    capabilities = response.json()
    assert "greenhouse" in capabilities
    assert "lever" in capabilities
    assert "manual" in capabilities


def test_greenhouse_source_creation_and_health(client, auth_headers):
    response = client.post(
        "/api/v1/jobs/sources",
        headers=auth_headers,
        json={
            "name": "Acme Board",
            "source_type": "greenhouse",
            "config": {"company_token": "acme"},
        },
    )
    assert response.status_code == 200
    source_id = response.json()["id"]

    health = client.post(
        f"/api/v1/jobs/sources/{source_id}/health", headers=auth_headers
    )
    assert health.status_code == 200
    # Health must be honestly reported (may be unavailable offline).
    assert "available" in health.json()


def test_saved_search_crud(client, auth_headers):
    response = client.post(
        "/api/v1/jobs/searches",
        headers=auth_headers,
        json={
            "name": "Remote Python",
            "query": "python",
            "filters": {"workplace_type": "remote"},
        },
    )
    assert response.status_code == 200
    search_id = response.json()["id"]
    searches = client.get("/api/v1/jobs/searches", headers=auth_headers).json()
    assert any(s["id"] == search_id for s in searches)
    client.delete(f"/api/v1/jobs/searches/{search_id}", headers=auth_headers)
