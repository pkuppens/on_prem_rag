"""Simple metadata management using SQLite — COMPATIBILITY SHIM.

.. deprecated::
   Import from ``backend.ingestion.infrastructure.metadata_store`` instead.
   This module is a compatibility shim for the Ingestion BC extraction (Phase 3).
"""

from __future__ import annotations

from backend.ingestion.infrastructure.metadata_store import (  # noqa: F401
    Base,
    DocumentRecord,
    EmbeddingRecord,
    MetadataStore,
)
