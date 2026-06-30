import os
from typing import Any

import httpx

from ..utils.tokenizer import estimate_tokens
from .base import ProviderBase
from .response import make_success_response
from .retry import with_retry

GEMINI_MODEL_MAP = {
    "gemini-1.5-flash": "gemini-1.5-flash",
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-2.0-flash": "gemini-2.0-flash-exp",
}


class GeminiProvider(ProviderBase):
    name = "gemini"
    default_model = "gemini-1.5-flash"

    def __init__(
        self,
        api_key: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._client = httpx.Client(timeout=120.0)

    @with_retry(max_retries=3, base_delay=1.0)
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict[str, Any]:
        model = GEMINI_MODEL_MAP.get(model or self.default_model, model or self.default_model)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        gemini_contents = self._convert_messages(messages)
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        resp = self._client.post(
            url,
            headers={"x-goog-api-key": self.api_key},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        candidate = data.get("candidates", [{}])[0]
        content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
        usage = data.get("usageMetadata", {})
        return make_success_response(
            content=content,
            model=model,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            raw=data,
        )

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            gemini_role = "model" if role in ("assistant", "model") else "user"
            text = msg.get("content", "")
            if text:
                contents.append(
                    {
                        "role": gemini_role,
                        "parts": [{"text": text}],
                    }
                )
        return contents

    def count_tokens(self, text: str, model: str | None = None) -> int:
        return estimate_tokens(text)

    @classmethod
    def from_env(cls) -> "GeminiProvider":
        return cls(api_key=os.environ.get("GEMINI_API_KEY"))
