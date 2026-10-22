"""Schemas for AI providers, usage, and settings."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AIProviderCreate(BaseModel):
    name: str
    provider: Literal["ollama", "openai_compatible"]
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    is_local: bool = False
    is_default: bool = False
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    timeout_seconds: float = Field(default=120.0, ge=1.0, le=1800.0)
    retries: int = Field(default=2, ge=0, le=10)
    task_models: dict | None = None
    disclosure_acknowledged: bool = False


class AIProviderUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    is_local: bool | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_seconds: float | None = None
    retries: int | None = None
    task_models: dict | None = None
    enabled: bool | None = None
    is_default: bool | None = None
    disclosure_acknowledged: bool | None = None


class AIProviderOut(BaseModel):
    id: int
    name: str
    provider: str
    base_url: str | None = None
    model: str | None = None
    models: list | None = None
    is_local: bool
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_seconds: float | None = None
    retries: int | None = None
    task_models: dict | None = None
    is_default: bool
    enabled: bool
    status: str | None = None
    last_tested: datetime | None = None
    error_message: str | None = None
    has_api_key: bool = False
    disclosure_acknowledged: bool = False

    model_config = {"from_attributes": True}


class ProviderTestResult(BaseModel):
    ok: bool
    provider: str
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None
    sample: str | None = None


class AIUsageRecordOut(BaseModel):
    id: int
    provider: str | None = None
    model: str | None = None
    task: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    duration_ms: int | None = None
    status: str | None = None
    error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SettingsOut(BaseModel):
    theme: str = "system"
    review_rounds: int = 2
    match_weights: dict = {}
    scheduler_enabled: bool = True
    max_daily_recommendations: int = 10
    notifications_enabled: bool = True
    default_template_id: str = "ats_friendly"
    match_category_thresholds: dict = {}


class SettingsUpdate(BaseModel):
    theme: str | None = None
    review_rounds: int | None = None
    match_weights: dict | None = None
    scheduler_enabled: bool | None = None
    max_daily_recommendations: int | None = None
    notifications_enabled: bool | None = None
    default_template_id: str | None = None
    match_category_thresholds: dict | None = None
