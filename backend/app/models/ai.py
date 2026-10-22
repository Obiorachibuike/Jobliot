"""AI provider configuration, usage records, background tasks, app settings."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AIProviderKind(str, Enum):
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"


class AIProviderConfiguration(Base, TimestampMixin):
    """Configuration for one AI provider.

    API keys are never stored in this table.  They live in the OS
    keyring (when available) or the encrypted secrets file, referenced
    here by a credential key.
    """

    __tablename__ = "ai_provider_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # user-visible label
    provider: Mapped[str] = mapped_column(
        SAEnum(AIProviderKind, values_callable=lambda e: [e.value for e in e])
    )
    base_url: Mapped[str | None] = mapped_column(String(500))
    model: Mapped[str | None] = mapped_column(String(200))
    models: Mapped[list | None] = mapped_column(JSON, default=list)
    is_local: Mapped[bool] = mapped_column(Boolean, default=False)
    temperature: Mapped[float | None] = mapped_column(Float, default=0.3)
    max_tokens: Mapped[int | None] = mapped_column(Integer, default=2048)
    timeout_seconds: Mapped[float | None] = mapped_column(Float, default=120.0)
    retries: Mapped[int | None] = mapped_column(Integer, default=2)
    task_models: Mapped[dict | None] = mapped_column(JSON, default=dict)  # task -> model override
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str | None] = mapped_column(String(30), default="untested")
    last_tested: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    credential_key: Mapped[str | None] = mapped_column(String(200))  # key in secret store
    disclosure_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class AIUsageRecord(Base, TimestampMixin):
    __tablename__ = "ai_usage_records"
    __table_args__ = (Index("ix_ai_usage_created", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str | None] = mapped_column(String(60))
    model: Mapped[str | None] = mapped_column(String(200))
    task: Mapped[str | None] = mapped_column(String(60))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String(30))  # ok/error
    error: Mapped[str | None] = mapped_column(Text)


class BackgroundTask(Base, TimestampMixin):
    __tablename__ = "background_tasks"
    __table_args__ = (Index("ix_background_task_status", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(30))  # queued/running/completed/failed/cancelled
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100 when measurable
    progress_label: Mapped[str | None] = mapped_column(String(200))
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[dict | None] = mapped_column(JSON, default=dict)
    cancellable: Mapped[bool] = mapped_column(Boolean, default=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict | None] = mapped_column(JSON, default=dict)


class AppSetting(Base, TimestampMixin):
    """Single-row application settings (theme, weights, workflow prefs)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
