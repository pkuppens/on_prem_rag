"""LLM Gateway Bounded Context.

Provides LLM interaction abstractions: text generation, streaming, health checks.
Routes to local or cloud providers.
"""

from backend.llm_gateway.application.completion_service import CompletionService
from backend.llm_gateway.domain.interfaces import EmbeddingProvider, LLMProvider, StreamingLLMProvider
from backend.llm_gateway.domain.value_objects import (
    Completion,
    CompletionChunk,
    ModelIdentifier,
    ModelNotFoundError,
    Prompt,
    TokenUsage,
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
    "CompletionService",
]
