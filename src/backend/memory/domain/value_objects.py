"""Domain value objects for the Memory bounded context.

This module defines the core value objects used throughout the memory system:
- MemoryDocument: A document stored in vector memory
- SearchResult: A result from a memory search
- MemoryType: Enumeration of memory entry types
- Importance: Importance score value object
- AccessLevel: Enumeration of access levels
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MemoryType(Enum):
    """Types of memory entries.

    Each memory entry has a type that describes what kind of information it holds.
    """

    FACT = "fact"
    OBSERVATION = "observation"
    RESULT = "result"
    CONTEXT = "context"
    GENERAL = "general"
    ENTITY_SOURCE = "entity_source"

    @classmethod
    def _missing_(cls, value: str) -> "MemoryType | None":
        """Case-insensitive lookup for backward compatibility with string values."""
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return None


class AccessLevel(Enum):
    """Memory access levels.

    Determines what operations an agent can perform on memory.
    """

    NONE = "none"  # No access
    READ = "read"  # Read-only access
    WRITE = "write"  # Read and write access
    ADMIN = "admin"  # Full access including delete


@dataclass(frozen=True)
class Importance:
    """Importance score for a memory entry.

    Value must be between 0.0 (lowest) and 1.0 (highest).
    Provides factory methods for common importance levels.
    """

    value: float

    def __post_init__(self) -> None:
        """Validate importance is in [0.0, 1.0]."""
        if not 0.0 <= self.value <= 1.0:
            msg = f"Importance must be between 0.0 and 1.0, got {self.value}"
            raise ValueError(msg)

    @classmethod
    def high(cls) -> "Importance":
        """Create a high importance value (0.8)."""
        return cls(0.8)

    @classmethod
    def medium(cls) -> "Importance":
        """Create a medium importance value (0.5)."""
        return cls(0.5)

    @classmethod
    def low(cls) -> "Importance":
        """Create a low importance value (0.2)."""
        return cls(0.2)


@dataclass
class MemoryDocument:
    """A document stored in vector memory.

    Represents a single memory entry with its content, metadata,
    and semantic embedding (handled by the vector store).

    Attributes:
        id: Unique document identifier
        content: The text content of the memory
        agent_role: The agent role that created this memory
        session_id: The session this memory belongs to
        memory_type: Type of memory ("fact", "observation", "result", "context", etc.)
        importance: Importance score (0.0 to 1.0)
        metadata: Additional metadata key-value pairs
        created_at: When this memory was created
    """

    id: str
    content: str
    agent_role: str
    session_id: str
    memory_type: str = "general"
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_metadata(self) -> dict[str, Any]:
        """Convert to ChromaDB-compatible metadata format.

        Returns:
            Dictionary with all fields serialized for ChromaDB metadata storage.
        """
        return {
            "agent_role": self.agent_role,
            "session_id": self.session_id,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            **{k: json.dumps(v) if isinstance(v, dict | list) else str(v) for k, v in self.metadata.items()},
        }


@dataclass
class SearchResult:
    """Result from a memory search.

    Contains the matched document content along with its distance from
    the query vector. The similarity property converts distance to a
    similarity score for easier interpretation.

    Attributes:
        id: The document ID
        content: The text content
        distance: Distance from query vector (lower is more similar)
        metadata: Document metadata
    """

    id: str
    content: str
    distance: float
    metadata: dict[str, Any]

    @property
    def similarity(self) -> float:
        """Convert distance to similarity score (0-1, higher is better).

        Assumes cosine distance where 0 = identical, 1 = orthogonal.
        """
        return max(0.0, 1.0 - self.distance)
