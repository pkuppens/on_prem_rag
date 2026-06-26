"""Compatibility shim — re-exports from the new LLM Gateway bounded context.

This file is kept for backward compatibility during the migration.
Import from ``backend.llm_gateway`` directly for new code.
"""

from backend.llm_gateway import *  # noqa: F401, F403
from backend.llm_gateway.infrastructure import (  # noqa: F401
    LiteLLMProvider,
    LLMProviderFactory,
    OllamaProvider,
    get_llm_provider_from_env,
)

__all__ = [
    "LLMProvider",
    "StreamingLLMProvider",
    "EmbeddingProvider",
    "ModelNotFoundError",
    "ModelIdentifier",
    "Prompt",
    "Completion",
    "CompletionChunk",
    "TokenUsage",
    "OllamaProvider",
    "LiteLLMProvider",
    "LLMProviderFactory",
    "get_llm_provider_from_env",
    "CompletionService",
]
