from abc import ABC, abstractmethod
from typing import Any


class ProviderBase(ABC):
    """Abstract base class for LLM providers."""

    name: str = "base"
    default_model: str = ""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict[str, Any]: ...

    def execute_tool(self, tool_call: dict) -> Any:
        raise NotImplementedError("Tool execution not implemented by this provider")

    @abstractmethod
    def count_tokens(self, text: str, model: str | None = None) -> int: ...

    @classmethod
    def from_env(cls) -> "ProviderBase":
        raise NotImplementedError
