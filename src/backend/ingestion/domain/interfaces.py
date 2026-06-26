"""Port interfaces (outbound ports) for the Ingestion Bounded Context.

These are interfaces that the Ingestion BC depends ON — they are implemented
by infrastructure adapters or by other bounded contexts.

Following the hexagonal architecture pattern:
- ``IDocumentLoader`` — load files into domain documents
- ``IChunker`` — split documents into chunks
- ``IEmbeddingGenerator`` — generate embeddings from chunks
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from backend.ingestion.domain.value_objects import Chunk, IngestionDocument


class IDocumentLoader(ABC):
    """Port for loading files into domain documents.

    Implementations handle specific file formats (PDF, DOCX, MD, TXT, HTML)
    and return domain ``IngestionDocument`` objects.
    """

    @abstractmethod
    def load_document(
        self,
        file_path: str | Path,
        *,
        params_key: str = "default",
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[list[IngestionDocument], dict[str, Any]]:
        """Load a document and return its content and metadata.

        Args:
            file_path: Path to the document file.
            params_key: Identifier for the parameter set used.
            progress_callback: Optional callback(page_num, total_pages).

        Returns:
            Tuple of (list of IngestionDocument, metadata dict).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or invalid.
            OSError: If file processing fails.
        """
        ...


class IChunker(ABC):
    """Port for chunking documents.

    Implementations split domain documents into smaller ``Chunk`` objects
    using various strategies (character, semantic, recursive).
    """

    @abstractmethod
    def chunk(
        self,
        documents: list[IngestionDocument],
        *,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        source_path: str | Path | None = None,
        enable_text_cleaning: bool = True,
        min_chunk_length: int = 10,
        strategy: str = "character",
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[Chunk]:
        """Split documents into chunks.

        Args:
            documents: List of domain documents to chunk.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap.
            source_path: Optional source path for metadata.
            enable_text_cleaning: Whether to clean chunk text.
            min_chunk_length: Minimum chunk length after cleaning.
            strategy: Chunking strategy name.
            progress_callback: Optional callback(page_num, total_pages).

        Returns:
            List of Chunk objects.
        """
        ...


class IEmbeddingGenerator(ABC):
    """Port for generating embeddings from chunk text.

    Implementations connect to embedding models (via LLM Gateway's
    ``EmbeddingProvider`` or similar) and produce vector embeddings.
    """

    @abstractmethod
    def generate_embeddings(
        self,
        chunks: list[Chunk],
        model_name: str,
        *,
        progress_callback: Callable[[float], None] | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for a list of chunks.

        Args:
            chunks: Domain Chunk objects with text to embed.
            model_name: Name of the embedding model.
            progress_callback: Optional callback(progress 0.0-1.0).

        Returns:
            List of embedding vectors, one per chunk.
        """
        ...
