"""ICompletionService port — interface for LLM Gateway BC.

The Query Service uses this port to generate answers from LLMs
and to compute embeddings for query encoding.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any


class ICompletionService(ABC):
    """Port for LLM completion operations.

    Implementations connect to the LLM Gateway BC to generate
    text completions, both non-streaming and streaming.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a complete response for a prompt.

        Args:
            prompt: The prompt text.

        Returns:
            Generated text response.
        """
        ...

    @abstractmethod
    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Stream a response token by token.

        Args:
            prompt: The prompt text.

        Yields:
            Partial content strings.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is healthy.

        Returns:
            True if healthy.
        """
        ...


class IEmbeddingPort(ABC):
    """Port for text embedding operations.

    Implementations connect to the LLM Gateway BC's embedding
    providers to encode query text for vector search.
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
