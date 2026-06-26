# src/backend/memory/vector_memory.py
"""Backward-compatibility shim for vector memory.

Symbols are now defined in:
- backend.memory.infrastructure.vector_memory (VectorMemory, DefaultEmbeddingFunction)
- backend.memory.domain.value_objects (MemoryDocument, SearchResult)

This shim re-exports from the canonical locations so existing imports continue to work.
"""

from __future__ import annotations

from backend.memory.domain.value_objects import MemoryDocument, SearchResult  # noqa: F401
from backend.memory.infrastructure.vector_memory import (  # noqa: F401
    DefaultEmbeddingFunction,
    VectorMemory,
)
