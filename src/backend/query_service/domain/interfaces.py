"""Port interfaces for the Query Service bounded context.

Defines the IQueryOrchestrator port that the API layer depends on,
and supporting interfaces for the anti-corruption layer adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from backend.query_service.domain.entities import Answer, Query


class IQueryOrchestrator(ABC):
    """Primary inbound port for the Query Service.

    Defines the contract for the RAG query workflow that the API layer
    depends on. Implemented by QueryOrchestrator in the application layer.
    """

    @abstractmethod
    def ask_question(
        self,
        question: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        strategy: str | None = None,
    ) -> dict[str, Any]:
        """Ask a question and get an answer with sources.

        Args:
            question: The question to ask.
            top_k: Maximum number of chunks to retrieve.
            similarity_threshold: Minimum similarity score.
            strategy: Optional retrieval strategy override.

        Returns:
            Dict containing answer, sources, and metadata.
        """
        ...

    @abstractmethod
    def retrieve_relevant_chunks(
        self,
        question: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant document chunks for a question.

        Args:
            question: The question to search for.
            top_k: Maximum number of chunks.
            similarity_threshold: Minimum similarity score.
            strategy: Optional retrieval strategy override.

        Returns:
            List of relevant chunks with metadata.
        """
        ...

    @abstractmethod
    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate an answer using LLM based on question and context.

        Args:
            question: The question to answer.
            context_chunks: Relevant document chunks as context.
            conversation_history: Optional prior messages.

        Returns:
            Generated answer text.
        """
        ...

    @abstractmethod
    def generate_answer_stream(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Generator[str, None, None]:
        """Stream answer tokens from LLM.

        Args:
            question: The question to answer.
            context_chunks: Relevant document chunks as context.
            conversation_history: Optional prior messages.

        Yields:
            Answer text chunks as they arrive.
        """
        ...
