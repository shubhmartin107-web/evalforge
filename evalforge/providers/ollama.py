import os
from typing import Any

import httpx

from ..utils.tokenizer import estimate_tokens
from .base import ProviderBase
from .response import make_success_response
from .retry import with_retry


class OllamaProvider(ProviderBase):
    name = "ollama"
    default_model = "llama3.1"

    def __init__(self, base_url: str | None = None, **kwargs):
        self.base_url = base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self._client = httpx.Client(timeout=300.0)

    @with_retry(max_retries=2, base_delay=2.0, max_delay=30.0)
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
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        resp = self._client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        input_tokens = estimate_tokens(str(messages))
        output_tokens = estimate_tokens(content)
        return make_success_response(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw=data,
        )

    def count_tokens(self, text: str, model: str | None = None) -> int:
        return estimate_tokens(text)

    @classmethod
    def from_env(cls) -> "OllamaProvider":
        return cls(base_url=os.environ.get("OLLAMA_URL"))
