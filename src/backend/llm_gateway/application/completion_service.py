"""Application service for LLM completion orchestration.

Coordinates the full completion workflow:
get provider → generate response → return result.
"""

from __future__ import annotations

from typing import Iterator

from backend.llm_gateway.domain.interfaces import LLMProvider, StreamingLLMProvider


class CompletionService:
    """Application service that orchestrates LLM completion.

    Wraps a provider and provides convenience methods for generation,
    streaming, and health checking.

    Usage:
        provider = LiteLLMProvider(model="ollama/mistral")
        service = CompletionService(provider)
        answer = service.generate("What is RAG?")
    """

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize with an LLM provider implementation.

        Args:
            provider: Any LLMProvider implementation.
        """
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        """The underlying LLM provider instance."""
        return self._provider

    def generate(self, prompt: str) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: The prompt text to send to the LLM.

        Returns:
            Generated answer text.
        """
        return self._provider.generate_answer(prompt)

    def generate_stream(self, prompt: str) -> Iterator[str]:
        """Stream a completion for the given prompt.

        Args:
            prompt: The prompt text to send to the LLM.

        Yields:
            Partial content strings as they arrive.
        """
        if isinstance(self._provider, StreamingLLMProvider):
            yield from self._provider.generate_answer_stream(prompt)
        else:
            yield self._provider.generate_answer(prompt)

    async def health_check(self) -> bool:
        """Check if the provider is healthy.

        Returns:
            True if the provider is reachable and responsive.
        """
        return await self._provider.health_check()
