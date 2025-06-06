import os
from dataclasses import dataclass


@dataclass
class VectorStoreConfig:
    """Configuration for vector store selection."""

    implementation: str = os.getenv("VECTOR_STORE_IMPL", "chroma")
    host: str | None = os.getenv("CHROMA_HOST")
    port: int | None = int(os.getenv("CHROMA_PORT", "0")) or None
    persist_directory: str = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
    collection_name: str = os.getenv("CHROMA_COLLECTION", "documents")
