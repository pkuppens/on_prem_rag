"""Adapter to the LLM Gateway BC.

Connects the Query Service's ICompletionService port to the
LLM Gateway BC's CompletionService and LLMProvider.
"""

from __future__ import annotations

from collections.abc import Generator

from backend.llm_gateway.application.completion_service import CompletionService
from backend.llm_gateway.domain.interfaces import LLMProvider
from backend.query_service.ports.llm_gateway import ICompletionService


class LLMCompletionAdapter(ICompletionService):
    """Adapter that delegates to the LLM Gateway BC.

    Wraps a CompletionService (or raw LLMProvider) into the
    Query Service's ICompletionService port interface.
    """

    def __init__(self, completion_service: CompletionService | None = None, provider: LLMProvider | None = None) -> None:
        """Initialize with a CompletionService or LLMProvider.

        Args:
            completion_service: Pre-configured CompletionService.
            provider: Alternatively, a raw LLMProvider (wraps into
                a CompletionService automatically).
        """
        if completion_service is not None:
            self._service = completion_service
        elif provider is not None:
            self._service = CompletionService(provider)
        else:
            from backend.llm_gateway.infrastructure.provider_factory import get_llm_provider_from_env

            self._service = CompletionService(get_llm_provider_from_env())

    def generate(self, prompt: str) -> str:
        """Generate a complete response.

        Args:
            prompt: The prompt text.

        Returns:
            Generated text response.
        """
        return self._service.generate(prompt)

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Stream a response token by token.

        Args:
            prompt: The prompt text.

        Yields:
            Partial content strings.
        """
        yield from self._service.generate_stream(prompt)

    async def health_check(self) -> bool:
        """Check if the LLM service is healthy.

        Returns:
            True if healthy.
        """
        return await self._service.health_check()

    @property
    def provider(self) -> LLMProvider:
        """Access the underlying LLM provider.

        Used for direct access to provider-specific features like
        generate_answer_stream.
        """
        return self._service.provider
