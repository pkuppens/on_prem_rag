"""IAuditTrail port — interface for Audit Trail BC.

The Query Service uses this port to log query events and answers
for compliance and traceability.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IAuditTrail(ABC):
    """Port for audit trail logging.

    Implementations connect to the Audit Trail BC to record
    query events, access checks, PII sanitization, and LLM interactions.
    """

    @abstractmethod
    def log_query_received(self, query_id: str, question: str, user_id: str, session_id: str) -> None:
        """Log that a query was received.

        Args:
            query_id: Unique query identifier.
            question: The question text (snippet for audit).
            user_id: The user who asked.
            session_id: The conversation session.
        """
        ...

    @abstractmethod
    def log_retrieval(self, query_id: str, chunk_count: int, strategy: str) -> None:
        """Log that context retrieval was performed.

        Args:
            query_id: The query identifier.
            chunk_count: Number of chunks retrieved.
            strategy: Retrieval strategy used.
        """
        ...

    @abstractmethod
    def log_answer(self, query_id: str, question: str, answer: str, confidence: str) -> None:
        """Log that an answer was generated.

        Args:
            query_id: The query identifier.
            question: The original question.
            answer: The generated answer (snippet for audit).
            confidence: Confidence level.
        """
        ...

    @abstractmethod
    def log_error(self, query_id: str, error: str, stage: str) -> None:
        """Log an error during query processing.

        Args:
            query_id: The query identifier.
            error: Error message.
            stage: The stage where the error occurred.
        """
        ...
