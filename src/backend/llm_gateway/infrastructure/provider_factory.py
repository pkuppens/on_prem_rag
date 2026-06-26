"""Factory for creating LLM providers from configuration.

Provides both a static factory method for direct provider creation
and an env-var-driven factory for runtime configuration.
"""

from __future__ import annotations

from backend.llm_gateway.domain.interfaces import LLMProvider  # noqa: F401
from backend.llm_gateway.infrastructure.litellm_provider import LiteLLMProvider
from backend.llm_gateway.infrastructure.ollama_provider import OllamaProvider


class LLMProviderFactory:
    """Factory for creating legacy LLM providers (Ollama direct, not LiteLLM).

    For production use, prefer get_llm_provider_from_env() which creates
    a LiteLLMProvider configured from environment variables.
    """

    @staticmethod
    def create_provider(provider_type: str, model_name: str, config: dict) -> LLMProvider:
        """Create a legacy provider by type.

        Args:
            provider_type: One of 'ollama', 'llamacpp', 'huggingface'.
            model_name: Name of the model to use.
            config: Provider-specific configuration dictionary.

        Returns:
            Configured LLMProvider instance.

        Raises:
            ValueError: If provider_type is unknown.
        """
        if provider_type == "ollama":
            return OllamaProvider(model_name, config)
        if provider_type == "llamacpp":
            raise NotImplementedError("LlamaCppProvider not yet migrated to llm_gateway")
        if provider_type == "huggingface":
            raise NotImplementedError("HuggingFaceProvider not yet migrated to llm_gateway")
        raise ValueError(f"Unknown provider type: {provider_type}")


def get_llm_provider_from_env() -> LLMProvider:
    """Create LLM provider from LLM_BACKEND and LLM_MODEL env vars.

    Uses LiteLLM for ollama, openai, anthropic, azure, huggingface.
    For backward compatibility, OLLAMA_MODEL and OLLAMA_BASE_URL are used when
    LLM_BACKEND is ollama and LLM_MODEL is not set.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If LLM_BACKEND is unknown.
    """
    from backend.llm_gateway.infrastructure.config import get_llm_config

    config = get_llm_config()
    return LiteLLMProvider(
        model=config.litellm_model,
        api_base=config.api_base,
    )
