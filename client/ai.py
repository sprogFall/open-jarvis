from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib import error, request


class AIRequestError(RuntimeError):
    """Raised when the configured AI provider cannot complete the request."""


@dataclass(slots=True)
class AIModelConfig:
    provider: str
    model: str
    api_key: str
    base_url: str | None = None

    def normalized_provider(self) -> str:
        return self.provider.strip().lower()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "AIModelConfig | None":
        if not payload:
            return None
        provider = str(payload.get("provider", "")).strip()
        model = str(payload.get("model", "")).strip()
        api_key = str(payload.get("api_key", "")).strip()
        base_url = payload.get("base_url")
        if not provider or not model or not api_key:
            return None
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=str(base_url).strip() or None if base_url is not None else None,
        )


def coerce_ai_config(payload: AIModelConfig | dict[str, Any] | None) -> AIModelConfig | None:
    if payload is None:
        return None
    if isinstance(payload, AIModelConfig):
        return payload
    return AIModelConfig.from_dict(payload)


class StructuredModelClient:
    def __init__(self, config: AIModelConfig) -> None:
        self.config = config

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        provider = self.config.normalized_provider()
        if provider == "anthropic":
            return self._invoke_anthropic(system_prompt=system_prompt, user_prompt=user_prompt)
        return self._invoke_openai_compatible(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _invoke_openai_compatible(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        endpoint = self.config.base_url or "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = self._post_json(
            endpoint,
            payload,
            {
                "Authorization": f"Bearer {self.config.api_key}",
            },
        )
        content = response["choices"][0]["message"]["content"]
        if isinstance(content, list):
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )
        else:
            text = str(content)
        return self._parse_json_text(text)

    def _invoke_anthropic(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        endpoint = self.config.base_url or "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.config.model,
            "system": system_prompt,
            "max_tokens": 1200,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
        response = self._post_json(
            endpoint,
            payload,
            {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        text = "".join(
            block.get("text", "")
            for block in response.get("content", [])
            if isinstance(block, dict)
        )
        return self._parse_json_text(text)

    @staticmethod
    def _parse_json_text(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIRequestError(f"AI response is not valid JSON: {text[:200]}") from exc
        if not isinstance(payload, dict):
            raise AIRequestError("AI response JSON must be an object")
        return payload

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        extra_headers: dict[str, str],
    ) -> dict[str, Any]:
        raw_request = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **extra_headers,
            },
            method="POST",
        )
        try:
            with request.urlopen(raw_request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIRequestError(
                f"AI provider returned HTTP {exc.code}: {body[:200]}"
            ) from exc
        except error.URLError as exc:
            raise AIRequestError(f"AI provider request failed: {exc.reason}") from exc
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise AIRequestError("AI provider returned non-JSON response") from exc
        if not isinstance(parsed, dict):
            raise AIRequestError("AI provider returned unexpected response body")
        return parsed
