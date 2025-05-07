"""Provider initialization module."""
from typing import Type, Dict

from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .deepseek_provider import DeepSeekProvider

# Register providers
PROVIDERS: Dict[str, Type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider
}

def get_provider(name: str) -> Type[LLMProvider]:
    """Get provider class by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available providers: {', '.join(PROVIDERS.keys())}")
    return PROVIDERS[name]

def list_providers() -> Dict[str, Type[LLMProvider]]:
    """Get dictionary of available providers."""
    return PROVIDERS.copy()