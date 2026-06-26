"""Domain value objects for the Query Service bounded context.

Immutable value objects representing query-level concepts:
query intent classification, confidence scoring, conversation context,
and other typed primitives that don't have their own identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class QueryIntent(Enum):
    """Classification of user query intent.

    Helps the orchestrator decide whether to:
    - Perform full RAG retrieval (INFORMATION_SEEKING)
    - Use conversation context only (CONTINUATION)
    - Route to a specific agent (AGENT_DISPATCH)
    """

    INFORMATION_SEEKING = auto()  # Needs RAG retrieval
    CONTINUATION = auto()  # Follow-up, conversational
    AGENT_DISPATCH = auto()  # Route to medical agent
    UNKNOWN = auto()  # Default fallback


@dataclass(frozen=True)
class Confidence:
    """Confidence score for an answer, derived from retrieval similarity.

    Attributes:
        label: Human-readable level (high/medium/low).
        score: Numerical average similarity from retrieval.
    """

    label: str = "low"
    score: float = 0.0

    @classmethod
    def from_average_similarity(cls, avg_similarity: float) -> Confidence:
        """Determine confidence level from average similarity score.

        Args:
            avg_similarity: Average similarity score from retrieved chunks.

        Returns:
            Confidence with appropriate label.
        """
        if avg_similarity > 0.8:
            return cls(label="high", score=avg_similarity)
        if avg_similarity > 0.6:
            return cls(label="medium", score=avg_similarity)
        return cls(label="low", score=avg_similarity)

    @classmethod
    def low(cls) -> Confidence:
        """Return a low confidence instance."""
        return cls(label="low", score=0.0)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {"label": self.label, "score": self.score}


@dataclass(frozen=True)
class ConversationContext:
    """Context for a multi-turn conversation.

    Stores recent messages to provide conversation history for the LLM.

    Attributes:
        messages: Recent conversation messages [{role, content}, ...].
        max_messages: Maximum number of messages to retain.
    """

    messages: tuple[dict[str, str], ...] = field(default_factory=tuple)
    max_messages: int = 6

    @classmethod
    def from_history(cls, history: list[dict[str, str]] | None, max_messages: int = 6) -> ConversationContext:
        """Create context from a history list, limiting to max_messages.

        Args:
            history: List of {role, content} dicts or None.
            max_messages: Maximum messages to include.

        Returns:
            ConversationContext instance.
        """
        if not history:
            return cls(messages=(), max_messages=max_messages)
        return cls(messages=tuple(history[-max_messages:]), max_messages=max_messages)

    @property
    def formatted(self) -> str:
        """Format messages as a human-readable conversation string."""
        if not self.messages:
            return ""
        lines = [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in self.messages]
        return "\n".join(lines)

    @property
    def is_empty(self) -> bool:
        """True if there are no messages."""
        return len(self.messages) == 0

    def to_list(self) -> list[dict[str, str]]:
        """Convert to list of dicts for API consumption."""
        return list(self.messages)
