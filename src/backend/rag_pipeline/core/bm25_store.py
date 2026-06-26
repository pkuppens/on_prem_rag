"""Compatibility shim — re-exports from ``backend.retrieval.infrastructure.bm25_store``.

All BM25 logic has been extracted to ``src/backend/retrieval/infrastructure/``
as part of the DDD bounded context extraction (Phase 2).

See docs/technical/DDD_EXTRACTION_PLAN.md#phase-2-retrieval-bc-extraction.
"""

from __future__ import annotations

from backend.retrieval.infrastructure.bm25_store import (  # noqa: F401
    BM25Store,
    _tokenize,
)
