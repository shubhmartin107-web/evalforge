import os
from typing import Any

import httpx

from ..utils.tokenizer import estimate_tokens
from .base import ProviderBase
from .response import make_success_response
from .retry import with_retry


class DeepSeekProvider(ProviderBase):
    name = "deepseek"
    default_model = "deepseek-chat"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com",
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url
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
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        resp = self._client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return make_success_response(
            content=choice["message"].get("content", ""),
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            tool_calls=choice["message"].get("tool_calls", []),
            raw=data,
        )

    def count_tokens(self, text: str, model: str | None = None) -> int:
        return estimate_tokens(text)

    @classmethod
    def from_env(cls) -> "DeepSeekProvider":
        return cls(api_key=os.environ.get("DEEPSEEK_API_KEY"))
