from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProviderType(StrEnum):
    deepseek = "deepseek"
    gemini = "gemini"
    groq = "groq"
    ollama = "ollama"
    anthropic = "anthropic"
    openai = "openai"
    custom = "custom"


class ProviderConfig(BaseModel):
    provider: ProviderType = ProviderType.deepseek
    model: str = "deepseek-chat"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_kwargs: dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    name: str = "default-agent"
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    system_prompt: str | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    max_steps: int = 50
    timeout_seconds: int = 300
