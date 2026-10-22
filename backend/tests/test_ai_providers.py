"""AI provider configuration, failure handling, and cost control tests."""

from __future__ import annotations

import pytest

from app.services.ai.adapters import parse_json_response
from app.services.ai.base import estimate_cost


def test_provider_creation(client, auth_headers):
    payload = {
        "name": "Local Ollama",
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "llama3.1",
        "is_local": True,
        "temperature": 0.2,
        "max_tokens": 1024,
        "timeout_seconds": 60,
        "retries": 1,
    }
    response = client.post("/api/v1/ai/providers", headers=auth_headers, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["is_local"] is True
    assert body["has_api_key"] is False
    assert "api_key" not in body


def test_provider_update_and_default_flag(client, auth_headers):
    payload = {
        "name": "Cloud LLM",
        "provider": "openai_compatible",
        "base_url": "https://api.example.com/v1",
        "model": "gpt-4o-mini",
        "api_key": "sk-test-12345",
        "is_local": False,
    }
    response = client.post("/api/v1/ai/providers", headers=auth_headers, json=payload)
    provider_id = response.json()["id"]
    assert response.json()["has_api_key"] is True

    # Update temperature only.
    response = client.patch(
        f"/api/v1/ai/providers/{provider_id}",
        headers=auth_headers,
        json={"temperature": 0.7},
    )
    assert response.json()["temperature"] == 0.7

    # The API key must never be returned.
    assert "api_key" not in response.json()


def test_provider_deletion(client, auth_headers):
    payload = {
        "name": "Temp Provider",
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "llama3.1",
        "is_local": True,
    }
    provider_id = client.post(
        "/api/v1/ai/providers", headers=auth_headers, json=payload
    ).json()["id"]
    response = client.delete(
        f"/api/v1/ai/providers/{provider_id}", headers=auth_headers
    )
    assert response.status_code == 200


def test_provider_health_check_reports_failure(client, auth_headers):
    payload = {
        "name": "Unreachable Ollama",
        "provider": "ollama",
        "base_url": "http://localhost:1",
        "model": "llama3.1",
        "is_local": True,
        "timeout_seconds": 2,
    }
    provider_id = client.post(
        "/api/v1/ai/providers", headers=auth_headers, json=payload
    ).json()["id"]
    response = client.post(
        f"/api/v1/ai/providers/{provider_id}/test", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]


def test_invalid_provider_kind_rejected(client, auth_headers):
    response = client.post(
        "/api/v1/ai/providers",
        headers=auth_headers,
        json={"name": "Bad", "provider": "unknown_provider"},
    )
    assert response.status_code == 422


def test_usage_records_are_listed(client, auth_headers):
    response = client.get("/api/v1/ai/usage", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_usage_summary_has_honest_cost(client, auth_headers):
    response = client.get("/api/v1/ai/usage/summary", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    # With no usage, cost must be None, not a fabricated number.
    assert body["total_requests"] == 0
    assert body["total_estimated_cost_usd"] is None


def test_estimate_cost_known_model():
    cost = estimate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost is not None
    assert cost > 0


def test_estimate_cost_unknown_model_returns_none():
    assert estimate_cost("totally-unknown-model", 100, 100) is None


def test_parse_json_response_tolerates_fences():
    text = '```json\n{"a": 1}\n```'
    assert parse_json_response(text) == {"a": 1}


def test_parse_json_response_plain():
    assert parse_json_response('{"b": 2}') == {"b": 2}


def test_parse_json_response_invalid():
    with pytest.raises(ValueError):
        parse_json_response("no json here")
