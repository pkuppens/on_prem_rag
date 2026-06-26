"""Domain entities for the Query Service bounded context.

Entities have identity and lifecycle:
- Query: A user's question with metadata
- Answer: The generated response
- Citation: Source document reference for a claim
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from backend.query_service.domain.value_objects import Confidence, QueryIntent


@dataclass
class Query:
    """A user's question with metadata.

    Represents a single question submitted to the RAG system.
    Has identity based on timestamp and session.

    Attributes:
        text: The raw question text.
        query_id: Unique identifier for this query.
        intent: Classification of the query intent.
        user_id: Optional identifier of the requesting user.
        session_id: Optional session identifier.
        timestamp: When the query was received.
        metadata: Additional optional metadata.
    """

    text: str
    query_id: str = ""
    intent: QueryIntent = QueryIntent.INFORMATION_SEEKING
    user_id: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """Check if the query text is empty or whitespace."""
        return not self.text.strip()

    def sanitized(self, max_length: int = 60) -> str:
        """Return truncated query for logging."""
        return self.text[:max_length] + "..." if len(self.text) > max_length else self.text

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for logging/audit."""
        return {
            "query_id": self.query_id,
            "text_snippet": self.sanitized(),
            "intent": self.intent.name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Answer:
    """The generated response to a user's query.

    Attributes:
        text: The answer text.
        citations: Source document references.
        confidence: Confidence score for the answer.
        chunks_retrieved: Number of retrieved chunks used.
        average_similarity: Average similarity of retrieved chunks.
        generated_at: When the answer was generated.
    """

    text: str
    citations: list[Citation] = field(default_factory=list)
    confidence: Confidence = field(default_factory=Confidence.low)
    chunks_retrieved: int = 0
    average_similarity: float = 0.0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def no_answer(cls, message: str = "I couldn't find relevant information to answer your question.") -> Answer:
        """Create a no-answer response when retrieval returns nothing."""
        return cls(
            text=message,
            confidence=Confidence.low(),
            chunks_retrieved=0,
            average_similarity=0.0,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for API response."""
        return {
            "answer": self.text,
            "sources": [c.to_dict() for c in self.citations],
            "confidence": self.confidence.label,
            "chunks_retrieved": self.chunks_retrieved,
            "average_similarity": self.average_similarity,
        }


@dataclass(frozen=True)
class Citation:
    """Reference to a source document supporting a claim in an answer.

    Attributes:
        document_name: Name of the source document.
        page_number: Page number within the document (if applicable).
        similarity_score: Retrieval similarity score.
        text_preview: Snippet of the source text.
    """

    document_name: str
    page_number: str | int
    similarity_score: float
    text_preview: str

    @classmethod
    def from_chunk(cls, chunk: dict[str, Any], preview_length: int = 200) -> Citation:
        """Create a Citation from a retrieval chunk dict.

        Args:
            chunk: Retrieval result dict with keys: document_name,
                page_number, similarity_score, text.
            preview_length: Max characters for text preview.

        Returns:
            Citation instance.
        """
        text = chunk.get("text", "")
        if len(text) > preview_length:
            text = text[:preview_length] + "..."

        return cls(
            document_name=str(chunk.get("document_name", "unknown")),
            page_number=chunk.get("page_number", chunk.get("page_label", "unknown")),
            similarity_score=float(chunk.get("similarity_score", 0.0)),
            text_preview=text,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for API response."""
        return {
            "document_name": self.document_name,
            "page_number": self.page_number,
            "similarity_score": self.similarity_score,
            "text_preview": self.text_preview,
        }
