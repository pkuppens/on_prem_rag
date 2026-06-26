"""Domain value objects for the Retrieval bounded context.

Defines the core types used throughout the retrieval pipeline:
QueryVector, SearchResult, SimilarityScore, RetrievalStrategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RetrievalStrategy(str, Enum):
    """Strategy selection for retrieval pipeline."""

    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
    BM25 = "bm25"


@dataclass
class QueryVector:
    """An embedding vector used as a search query."""

    vector: list[float]

    def __len__(self) -> int:
        return len(self.vector)


@dataclass
class SimilarityScore:
    """A normalized similarity score in [0, 1]."""

    score: float

    def is_pass(self, threshold: float = 0.0) -> bool:
        """Check whether this score meets the given threshold."""
        return self.score >= threshold

    def __float__(self) -> float:
        return self.score


@dataclass
class SearchResult:
    """A single search result from the retrieval pipeline."""

    text: str
    similarity_score: float
    document_id: str
    document_name: str
    chunk_index: int
    record_id: str
    page_number: str | int
    page_label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SearchResult:
        """Create a SearchResult from a dict (legacy compatibility)."""
        return cls(
            text=d.get("text", ""),
            similarity_score=d.get("similarity_score", 0.0),
            document_id=d.get("document_id", "unknown"),
            document_name=d.get("document_name", "unknown"),
            chunk_index=d.get("chunk_index", 0),
            record_id=d.get("record_id", ""),
            page_number=d.get("page_number", "unknown"),
            page_label=d.get("page_label", "unknown"),
            metadata={k: v for k, v in d.items() if k not in _RESERVED_KEYS},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a flat dict (legacy compatibility format)."""
        return {
            "text": self.text,
            "similarity_score": self.similarity_score,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "chunk_index": self.chunk_index,
            "record_id": self.record_id,
            "page_number": self.page_number,
            "page_label": self.page_label or "unknown",
            **self.metadata,
        }


_RESERVED_KEYS = frozenset(
    {
        "text",
        "similarity_score",
        "document_id",
        "document_name",
        "chunk_index",
        "record_id",
        "page_number",
        "page_label",
    }
)
