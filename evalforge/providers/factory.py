from ..models.provider import ProviderType
from .anthropic_provider import AnthropicProvider
from .base import ProviderBase
from .deepseek import DeepSeekProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider
from .openai_provider import OpenAIProvider

_PROVIDER_MAP: dict[ProviderType, type[ProviderBase]] = {
    ProviderType.deepseek: DeepSeekProvider,
    ProviderType.gemini: GeminiProvider,
    ProviderType.groq: GroqProvider,
    ProviderType.ollama: OllamaProvider,
    ProviderType.anthropic: AnthropicProvider,
    ProviderType.openai: OpenAIProvider,
}


def create_provider(provider_type: ProviderType | str, **kwargs) -> ProviderBase:
    if isinstance(provider_type, str):
        provider_type = ProviderType(provider_type)
    cls = _PROVIDER_MAP.get(provider_type)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_type}")
    return cls(**kwargs)


def get_provider_from_env(provider_type: ProviderType | str | None = None) -> ProviderBase:
    import os

    if provider_type is None:
        env_type = os.environ.get("EVALFORGE_PROVIDER", "deepseek")
        provider_type = ProviderType(env_type)
    elif isinstance(provider_type, str):
        provider_type = ProviderType(provider_type)
    return create_provider(provider_type)


__all__ = ["create_provider", "get_provider_from_env"]
