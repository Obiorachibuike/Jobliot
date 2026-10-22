"""Concrete AI provider adapters (Ollama, OpenAI-compatible)."""

from __future__ import annotations

import json
import logging

import httpx

from app.services.ai.base import (
    AIAdapter,
    CompletionResult,
    ProviderHealth,
    build_adapter,
    estimate_cost,
    register_adapter,
)
from app.services.ai.credentials import retrieve_secret

logger = logging.getLogger("careerpilot.ai")


class OllamaAdapter(AIAdapter):
    """Adapter for Ollama's OpenAI-compatible endpoint.

    Ollama runs models locally; nothing leaves the machine.
    """

    kind = "ollama"
    is_local = True

    def complete(self, messages: list[dict], task: str = "general") -> CompletionResult:
        model = self.model or "llama3.1"
        url = f"{self.base_url.rstrip('/') or 'http://localhost:11434'}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        import time as _time

        start = _time.monotonic()
        response = httpx.post(url, json=payload, timeout=self.timeout)
        latency_ms = int((_time.monotonic() - start) * 1000)
        response.raise_for_status()
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        text = choice.get("message", {}).get("content", "")
        usage = data.get("usage") or {}
        return CompletionResult(
            text=text,
            model=model,
            provider="ollama",
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency_ms=latency_ms,
        )

    def health_check(self) -> ProviderHealth:
        import time as _time

        base = self.base_url.rstrip("/") or "http://localhost:11434"
        start = _time.monotonic()
        try:
            response = httpx.get(f"{base}/api/tags", timeout=8.0)
            latency = int((_time.monotonic() - start) * 1000)
            if response.status_code != 200:
                return ProviderHealth(ok=False, error=f"HTTP {response.status_code}")
            models = [
                m.get("name", "") for m in (response.json().get("models") or [])
            ]
            if self.model and self.model not in models:
                return ProviderHealth(
                    ok=False, error=f"Model '{self.model}' not found locally", latency_ms=latency
                )
            return ProviderHealth(ok=True, model=self.model, latency_ms=latency)
        except Exception as exc:
            return ProviderHealth(ok=False, error=str(exc)[:300])


class OpenAICompatibleAdapter(AIAdapter):
    """Adapter for any OpenAI-compatible chat-completions API."""

    kind = "openai_compatible"
    is_local = False

    def complete(self, messages: list[dict], task: str = "general") -> CompletionResult:
        if not self.base_url:
            raise ValueError("OpenAI-compatible provider requires a base URL")
        model = self.model or "gpt-4o-mini"
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = self.api_key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        import time as _time

        start = _time.monotonic()
        response = httpx.post(url, json=payload, headers=headers, timeout=self.timeout)
        latency_ms = int((_time.monotonic() - start) * 1000)
        response.raise_for_status()
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        text = choice.get("message", {}).get("content", "")
        usage = data.get("usage") or {}
        return CompletionResult(
            text=text,
            model=model,
            provider="openai_compatible",
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency_ms=latency_ms,
        )

    def health_check(self) -> ProviderHealth:
        import time as _time

        start = _time.monotonic()
        try:
            result = self.complete(
                [{"role": "user", "content": "Reply with exactly: ok"}],
                task="health_check",
            )
            return ProviderHealth(
                ok=True, model=self.model, latency_ms=result.latency_ms
            )
        except Exception as exc:
            return ProviderHealth(ok=False, error=str(exc)[:300])


register_adapter("ollama", OllamaAdapter)
register_adapter("openai_compatible", OpenAICompatibleAdapter)


def parse_json_response(text: str) -> dict:
    """Parse a JSON object from an LLM response, tolerating fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)
        cleaned = cleaned[1] if len(cleaned) > 2 else cleaned[0]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in the response")
    return json.loads(cleaned[start : end + 1])


def get_provider_adapter(config_row) -> AIAdapter | None:
    """Build an adapter from a persisted configuration row."""
    config = {
        "name": config_row.name,
        "provider": config_row.provider,
        "base_url": config_row.base_url,
        "model": config_row.model,
        "temperature": config_row.temperature,
        "max_tokens": config_row.max_tokens,
        "timeout_seconds": config_row.timeout_seconds,
        "retries": config_row.retries,
        "credential_key": config_row.credential_key,
        "is_local": config_row.is_local,
    }
    return build_adapter(config)
