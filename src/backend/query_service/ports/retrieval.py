"""IRetrievalService port — interface for Retrieval BC.

The Query Service uses this port to search for relevant document
chunks based on the user's question.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IRetrievalService(ABC):
    """Port for document retrieval operations.

    Implementations connect to the Retrieval BC to perform semantic
    search over embedded document chunks using various strategies.
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant document chunks for a query.

        Args:
            query: The search query text.
            top_k: Maximum number of chunks to return.
            similarity_threshold: Minimum similarity score filter.
            strategy: Optional retrieval strategy override
                (dense, sparse, hybrid, bm25).

        Returns:
            List of result dicts with keys: text, similarity_score,
            document_name, chunk_index, page_number, etc.
        """
        ...
