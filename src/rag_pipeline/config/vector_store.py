import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VectorStoreConfig:
    """Configuration for vector store selection."""

    implementation: str = os.getenv("VECTOR_STORE_IMPL", "chroma")
    host: str | None = os.getenv("CHROMA_HOST")
    port: int | None = int(os.getenv("CHROMA_PORT", "0")) or None
    persist_directory: str | Path = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
    collection_name: str = os.getenv("CHROMA_COLLECTION", "documents")

    def __post_init__(self):
        """Convert persist_directory to Path if it's a string."""
        if isinstance(self.persist_directory, str):
            self.persist_directory = Path(self.persist_directory)
