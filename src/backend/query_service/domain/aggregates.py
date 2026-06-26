"""Conversation aggregate root for the Query Service.

A Conversation represents a multi-turn Q&A session between a user
and the RAG system. It tracks the message history and enforces
invariants about the interaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from backend.query_service.domain.entities import Answer, Query
from backend.query_service.domain.events import (
    AnswerGenerated,
    ContextRetrieved,
    DomainEvent,
    QueryReceived,
)
from backend.query_service.domain.value_objects import Confidence, ConversationContext


@dataclass
class Conversation:
    """Aggregate root for a multi-turn conversation session.

    Tracks the message history, enforces invariants about message
    ordering, and records domain events for each interaction step.

    Attributes:
        session_id: Unique identifier for the conversation session.
        user_id: Optional identifier of the user.
        messages: Ordered list of {role, content} messages.
        pending_events: Domain events waiting to be published.
        created_at: When the conversation started.
        updated_at: When the conversation was last modified.
    """

    session_id: str
    user_id: str = ""
    messages: list[dict[str, str]] = field(default_factory=list)
    pending_events: list[DomainEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_query(self, query: Query) -> QueryReceived:
        """Record a user query in the conversation.

        Records the query as a user message and emits a QueryReceived event.

        Args:
            query: The Query entity.

        Returns:
            QueryReceived domain event.
        """
        self.messages.append({"role": "user", "content": query.text})
        self.updated_at = datetime.now(timezone.utc)

        event = QueryReceived(
            query_id=query.query_id,
            text=query.text,
            user_id=query.user_id,
            session_id=query.session_id,
            timestamp=query.timestamp,
        )
        self.pending_events.append(event)
        return event

    def add_answer(self, query: Query, answer: Answer, chunks: list[dict[str, Any]]) -> AnswerGenerated:
        """Record an assistant answer in the conversation.

        Records the answer as an assistant message and emits an AnswerGenerated event.

        Args:
            query: The original Query entity.
            answer: The Answer entity.
            chunks: The retrieved chunks used for context.

        Returns:
            AnswerGenerated domain event.
        """
        self.messages.append({"role": "assistant", "content": answer.text})
        self.updated_at = datetime.now(timezone.utc)

        event = AnswerGenerated(
            query_id=query.query_id,
            question=query.text,
            answer=answer.text,
            confidence=answer.confidence.label,
            chunks_retrieved=answer.chunks_retrieved,
            average_similarity=answer.average_similarity,
            session_id=self.session_id,
        )
        self.pending_events.append(event)
        return event

    def add_context_retrieved(self, query_id: str, chunks: list[dict[str, Any]], strategy: str) -> ContextRetrieved:
        """Record that context was retrieved for a query.

        Args:
            query_id: The query identifier.
            chunks: Retrieved chunk data.
            strategy: The retrieval strategy used.

        Returns:
            ContextRetrieved domain event.
        """
        event = ContextRetrieved(
            query_id=query_id,
            chunk_count=len(chunks),
            strategy=strategy,
        )
        self.pending_events.append(event)
        return event

    def get_context(self, max_messages: int = 6) -> ConversationContext:
        """Get the conversation context for LLM prompt building.

        Args:
            max_messages: Maximum number of messages to include.

        Returns:
            ConversationContext with recent messages.
        """
        return ConversationContext.from_history(self.messages, max_messages)

    @property
    def last_user_message(self) -> str | None:
        """Get the content of the last user message, if any."""
        for msg in reversed(self.messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return None

    @property
    def message_count(self) -> int:
        """Total number of messages in the conversation."""
        return len(self.messages)

    def clear_events(self) -> list[DomainEvent]:
        """Clear and return all pending domain events.

        Typically called after publishing events to an event bus.
        """
        events = list(self.pending_events)
        self.pending_events.clear()
        return events
