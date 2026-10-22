"""AI provider configuration and usage API."""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.ai import AIProviderConfiguration, AIUsageRecord
from app.schemas.ai import AIProviderCreate, AIProviderOut, AIProviderUpdate, AIUsageRecordOut, ProviderTestResult
from app.services.ai.adapters import get_provider_adapter
from app.services.ai.credentials import delete_secret, retrieve_secret, store_secret

router = APIRouter(prefix="/api/v1/ai", dependencies=[TokenDep])


def _mask(config: AIProviderConfiguration) -> dict:
    data = {
        column: getattr(config, column)
        for column in AIProviderConfiguration.__table__.columns.keys()
    }
    data["has_api_key"] = bool(config.credential_key)
    data.pop("credential_key", None)
    return data


@router.get("/providers", response_model=list[AIProviderOut])
def list_providers(session: SessionDep):
    return [_mask(c) for c in session.query(AIProviderConfiguration).order_by(AIProviderConfiguration.id).all()]


@router.post("/providers", response_model=AIProviderOut)
def create_provider(payload: AIProviderCreate, session: SessionDep):
    if payload.is_default:
        _clear_default(session)

    credential_key = None
    if payload.api_key:
        credential_key = f"ai_provider_key_{int(time.time() * 1000)}"
        store_secret(credential_key, payload.api_key)

    config = AIProviderConfiguration(
        name=payload.name,
        provider=payload.provider,
        base_url=payload.base_url,
        model=payload.model,
        is_local=payload.is_local,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        timeout_seconds=payload.timeout_seconds,
        retries=payload.retries,
        task_models=payload.task_models or {},
        is_default=payload.is_default,
        enabled=True,
        disclosure_acknowledged=payload.disclosure_acknowledged,
        credential_key=credential_key,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return _mask(config)


@router.patch("/providers/{provider_id}", response_model=AIProviderOut)
def update_provider(provider_id: int, payload: AIProviderUpdate, session: SessionDep):
    config = session.get(AIProviderConfiguration, provider_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("api_key"):
        if config.credential_key:
            delete_secret(config.credential_key)
        credential_key = f"ai_provider_key_{int(time.time() * 1000)}"
        store_secret(credential_key, data.pop("api_key"))
        config.credential_key = credential_key
    if data.get("is_default"):
        _clear_default(session)
    for key, value in data.items():
        setattr(config, key, value)
    session.commit()
    session.refresh(config)
    return _mask(config)


@router.delete("/providers/{provider_id}")
def delete_provider(provider_id: int, session: SessionDep):
    config = session.get(AIProviderConfiguration, provider_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    if config.credential_key:
        delete_secret(config.credential_key)
    session.delete(config)
    session.commit()
    return {"ok": True}


@router.post("/providers/{provider_id}/test", response_model=ProviderTestResult)
def test_provider(provider_id: int, session: SessionDep):
    config = session.get(AIProviderConfiguration, provider_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    adapter = get_provider_adapter(config)
    if adapter is None:
        raise HTTPException(status_code=400, detail="Unknown provider kind")
    started = time.monotonic()
    health = adapter.health_check()
    config.status = "ok" if health.ok else "error"
    config.last_tested = datetime.utcnow()
    config.error_message = health.error
    session.commit()
    return ProviderTestResult(
        ok=health.ok,
        provider=config.provider,
        model=config.model,
        latency_ms=health.latency_ms,
        error=health.error,
        sample="Connection test completed." if health.ok else None,
    )


@router.get("/usage", response_model=list[AIUsageRecordOut])
def ai_usage(session: SessionDep, limit: int = 100):
    return (
        session.query(AIUsageRecord)
        .order_by(AIUsageRecord.id.desc())
        .limit(min(limit, 500))
        .all()
    )


@router.get("/usage/summary")
def ai_usage_summary(session: SessionDep):
    records = session.query(AIUsageRecord).all()
    total_tokens = sum(r.total_tokens or 0 for r in records)
    costs = [r.estimated_cost for r in records if r.estimated_cost is not None]
    by_task: dict[str, int] = {}
    for record in records:
        by_task[record.task or "unknown"] = by_task.get(record.task or "unknown", 0) + 1
    return {
        "total_requests": len(records),
        "total_tokens": total_tokens,
        "total_estimated_cost_usd": round(sum(costs), 4) if costs else None,
        "cost_note": None if costs else "Cost unknown for the configured model(s).",
        "by_task": by_task,
    }


def _clear_default(session: Session) -> None:
    for config in session.query(AIProviderConfiguration).filter(
        AIProviderConfiguration.is_default.is_(True)
    ):
        config.is_default = False


def get_default_adapter_config(session: Session) -> AIProviderConfiguration | None:
    """Return the default enabled provider configuration, if any."""
    default = (
        session.query(AIProviderConfiguration)
        .filter(AIProviderConfiguration.is_default.is_(True))
        .first()
    )
    if default is not None and default.enabled:
        return default
    enabled = (
        session.query(AIProviderConfiguration)
        .filter(AIProviderConfiguration.enabled.is_(True))
        .order_by(AIProviderConfiguration.id.asc())
        .first()
    )
    return enabled
