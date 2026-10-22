"""Core backend tests: startup, health, auth, persistence."""

from __future__ import annotations


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "sqlite"


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/profile")
    assert response.status_code == 401


def test_token_auth_roundtrip(client, auth_headers):
    response = client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] >= 1


def test_wrong_token_rejected(client):
    response = client.get("/api/v1/profile", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_settings_roundtrip(client, auth_headers):
    response = client.get("/api/v1/settings", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["theme"] == "system"

    response = client.patch(
        "/api/v1/settings", headers=auth_headers, json={"theme": "dark"}
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "dark"


def test_database_file_created(client, data_dir):
    # The lifespan (triggered by the client) runs migrations and creates the DB.
    from app.core.config import get_settings

    db_path = get_settings().database_path
    assert db_path.exists(), f"Database not found at {db_path}"


def test_foreign_keys_enforced(client, auth_headers):
    # SQLite FK enforcement is configured at connect time.
    from app.core.database import get_engine
    from sqlalchemy import text

    engine = get_engine()
    with engine.connect() as connection:
        result = connection.execute(text("PRAGMA foreign_keys")).scalar()
    assert result == 1
