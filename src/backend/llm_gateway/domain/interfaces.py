"""Port interfaces for the LLM Gateway bounded context.

Defines abstract base classes that infrastructure implementations must conform to.
Following the port/adapter pattern (hexagonal architecture).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator


class LLMProvider(ABC):
    """Abstract base class for LLM providers (port interface).

    Implementations connect to specific LLM backends (Ollama, OpenAI, etc.)
    and provide text generation and health checks.
    """

    @abstractmethod
    def generate_answer(self, prompt: str) -> str:
        """Return an answer for the given prompt.

        Args:
            prompt: The prompt text to send to the LLM.

        Returns:
            Generated answer text.

        Raises:
            RuntimeError: If generation fails.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is healthy and reachable."""
        ...


class StreamingLLMProvider(LLMProvider):
    """Extended interface for providers that support streaming responses."""

    @abstractmethod
    def generate_answer_stream(self, prompt: str) -> Iterator[str]:
        """Stream answer tokens from the LLM provider.

        Yields partial content strings as they arrive from the provider.

        Args:
            prompt: The prompt text to send to the LLM.

        Yields:
            Partial content strings (token- or chunk-level).

        Raises:
            RuntimeError: If streaming fails.
        """
        ...


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers (port interface).

    Implementations generate vector embeddings from text for use in
    vector search and similarity computation.
    """

    @abstractmethod
    def get_text_embedding(self, text: str) -> list[float]:
        """Return embedding vector for the given text.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        ...
