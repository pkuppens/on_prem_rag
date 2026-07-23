"""Vector store configuration (moved from rag_pipeline/config/vector_store.py)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VectorStoreConfig:
    """Configuration for vector store selection.

    Fields use ``default_factory`` (not a bare ``os.getenv(...)`` default) so each
    instantiation re-reads the environment. A plain default is evaluated once at
    class-definition/import time and bakes in whatever the env vars were then —
    e.g. test isolation that sets CHROMA_PERSIST_DIR per pytest-xdist worker in
    pytest_configure runs after this module is first imported, so a baked-in
    default would silently ignore it and all workers would share one sqlite file.
    """

    implementation: str = field(default_factory=lambda: os.getenv("VECTOR_STORE_IMPL", "chroma"))
    host: str | None = field(default_factory=lambda: os.getenv("CHROMA_HOST"))
    port: int | None = field(default_factory=lambda: int(os.getenv("CHROMA_PORT", "0")) or None)
    persist_directory: str | Path = field(default_factory=lambda: os.getenv("CHROMA_PERSIST_DIR", "data/chroma"))
    collection_name: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "documents"))

    def __post_init__(self):
        """Convert persist_directory to Path if it's a string."""
        if isinstance(self.persist_directory, str):
            self.persist_directory = Path(self.persist_directory)
