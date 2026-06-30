"""Anthropic/Claude provider with streaming, thinking blocks, and tool use support."""

import json
import os
from typing import Any

import httpx

from ..utils.tokenizer import estimate_tokens
from .base import ProviderBase
from .response import make_success_response
from .retry import with_retry

ANTHROPIC_MODELS = {
    "claude-3-5-haiku-20241022": {"input": 0.00080, "output": 0.00400},
    "claude-3-5-sonnet-20241022": {"input": 0.00300, "output": 0.01500},
    "claude-opus-4-20250514": {"input": 0.01500, "output": 0.07500},
    "claude-opus-4.5-20250610": {"input": 0.01500, "output": 0.07500},
}

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(ProviderBase):
    name = "anthropic"
    default_model = "claude-3-5-haiku-20241022"

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = httpx.Client(timeout=180.0)

    @with_retry(max_retries=3, base_delay=1.0)
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_budget: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        model = model or self.default_model
        system, msgs = self._split_system(messages)
        payload = self._build_payload(model, msgs, system, temperature, max_tokens, thinking_budget, kwargs)

        resp = self._client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        text, tool_calls = self._parse_content(data.get("content", []))

        return make_success_response(
            content=text,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_calls=tool_calls,
            raw=data,
        )

    def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Any:
        model = model or self.default_model
        system, msgs = self._split_system(messages)
        payload = self._build_payload(model, msgs, system, temperature, max_tokens, kwargs=kwargs)
        payload["stream"] = True

        with self._client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            json=payload,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield line

    def _split_system(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system = None
        msgs = []
        for m in messages:
            if m.get("role") == "system":
                if system is None:
                    system = m["content"]
                else:
                    system += "\n" + m["content"]
            else:
                msgs.append(m)
        return system, msgs

    def _build_payload(
        self,
        model: str,
        messages: list[dict],
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_budget: int | None = None,
        kwargs: dict | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        if thinking_budget:
            payload["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        if kwargs:
            payload.update(kwargs)
        return payload

    def _parse_content(self, content_blocks: list[dict]) -> tuple[str, list[dict]]:
        text = ""
        tool_calls = []
        for block in content_blocks:
            block_type = block.get("type", "")
            if block_type == "text":
                text += block.get("text", "")
            elif block_type == "thinking":
                thinking = block.get("thinking", "")
                text += f"<thinking>{thinking}</thinking>"
            elif block_type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    }
                )
            elif block_type == "tool_result":
                text += block.get("content", "")
        return text, tool_calls

    def count_tokens(self, text: str, model: str | None = None) -> int:
        return estimate_tokens(text)

    @classmethod
    def from_env(cls) -> "AnthropicProvider":
        return cls(api_key=os.environ.get("ANTHROPIC_API_KEY"))
