"""Provider adapters for SurveyGuard agents."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when a model provider request fails."""


class ChatProvider(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


@dataclass
class OpenAICompatibleProvider:
    base_url: str
    model: str
    api_key: str = "ollama"
    timeout_seconds: float = 60.0
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> OpenAICompatibleProvider:
        return cls(
            base_url=os.getenv("SURVEYGUARD_BASE_URL", "http://localhost:11434/v1"),
            model=os.getenv("SURVEYGUARD_MODEL", "qwen2.5:3b"),
            api_key=os.getenv("SURVEYGUARD_API_KEY", "ollama"),
            timeout_seconds=float(os.getenv("SURVEYGUARD_TIMEOUT_SECONDS", "60")),
        )

    def complete(self, *, system: str, user: str) -> str:
        endpoint = self.base_url.rstrip("/") + "/chat/completions"
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Model request failed: {exc}") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider response did not contain message content.") from exc


class ScriptedProvider:
    """Deterministic queued responses for tests; not used for scored claims."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict[str, str]] = []

    def complete(self, *, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        if not self._responses:
            raise ProviderError("No scripted response remains.")
        return self._responses.pop(0)
