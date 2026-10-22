"""AI provider adapter interface and registry."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.services.ai.credentials import retrieve_secret


@dataclass
class CompletionResult:
    text: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int = 0
    cached: bool = False


@dataclass
class ProviderHealth:
    ok: bool
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None


class AIAdapter(ABC):
    kind: str = "base"
    is_local: bool = False

    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("name", "provider")
        self.base_url = config.get("base_url") or ""
        self.model = config.get("model") or ""
        self.temperature = float(config.get("temperature", 0.3))
        self.max_tokens = int(config.get("max_tokens", 2048))
        self.timeout = float(config.get("timeout_seconds", 120.0))
        self.retries = int(config.get("retries", 2))
        self.credential_key = config.get("credential_key")
        self._api_key = None

    @property
    def api_key(self) -> str | None:
        if self._api_key is None and self.credential_key:
            self._api_key = retrieve_secret(self.credential_key)
        return self._api_key

    @abstractmethod
    def complete(self, messages: list[dict], task: str = "general") -> CompletionResult:
        ...

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        ...

    def _should_retry(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return any(
            marker in text
            for marker in ("429", "rate limit", "timeout", "503", "502", "500", "overloaded")
        )

    def complete_with_retry(self, messages: list[dict], task: str = "general") -> CompletionResult:
        """Bounded retries with exponential backoff for retryable errors."""
        import httpx

        attempts = self.retries + 1
        last_exc: Exception | None = None
        for attempt in range(attempts):
            started = time.monotonic()
            try:
                result = self.complete(messages, task=task)
                return result
            except Exception as exc:
                last_exc = exc
                if attempt < attempts - 1 and self._should_retry(exc):
                    delay = min(2.0 * (2**attempt), 15.0)
                    time.sleep(delay)
                else:
                    raise
        raise last_exc or RuntimeError("AI completion failed")


# ---------------------------------------------------------------------------
# pricing (USD per 1M tokens) - used only for *estimates*; if a model
# is unknown we report None rather than guessing a cost.
# ---------------------------------------------------------------------------

KNOWN_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-opus-20240229": (15.00, 75.00),
    "mistral-large-latest": (2.00, 6.00),
    "mistral-small-latest": (0.20, 0.60),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    pricing = KNOWN_PRICING.get(model.lower())
    if pricing is None:
        return None  # unknown pricing - never fabricate a cost
    input_rate, output_rate = pricing
    return round(
        (prompt_tokens / 1_000_000) * input_rate
        + (completion_tokens / 1_000_000) * output_rate,
        6,
    )


_ADAPTERS: dict[str, type[AIAdapter]] = {}


def register_adapter(kind: str, adapter_class: type[AIAdapter]) -> None:
    _ADAPTERS[kind] = adapter_class


def get_adapter_class(kind: str) -> type[AIAdapter] | None:
    return _ADAPTERS.get(kind)


def build_adapter(config: dict) -> AIAdapter | None:
    adapter_class = get_adapter_class(config.get("provider"))
    if adapter_class is None:
        return None
    return adapter_class(config)
