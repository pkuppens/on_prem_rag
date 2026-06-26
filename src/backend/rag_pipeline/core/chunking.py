"""Document chunking functionality for the RAG pipeline — COMPATIBILITY SHIM.

.. deprecated::
   The chunking logic has been moved to ``backend.ingestion.infrastructure.chunking``
   as part of the DDD bounded context extraction (Phase 3). This module now wraps
   that implementation while preserving the old API returning ``LlamaIndex Document``
   objects.

See docs/technical/CHUNKING.md for detailed chunking strategies, implementation
decisions, and performance considerations.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode

from backend.ingestion.domain.value_objects import IngestionDocument
from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.rag_pipeline.utils.text_cleaning import clean_chunk_text, get_text_statistics

logger = StructuredLogger(__name__)

# Separators for recursive chunking: try paragraph, line, then word boundaries.
RECURSIVE_SEPARATORS = ["\n\n", "\n", ". ", " "]


class ChunkingStrategy(Protocol):
    """Protocol for chunking strategies (Strategy pattern)."""

    def get_nodes_from_documents(self, documents: list[Document]) -> list[BaseNode]:
        """Split documents into nodes/chunks."""
        ...


def _create_character_strategy(chunk_size: int, chunk_overlap: int) -> ChunkingStrategy:
    """Create character-based strategy using RecursiveChunkingStrategy."""
    return RecursiveChunkingStrategy(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def _create_semantic_strategy(chunk_size: int, chunk_overlap: int) -> ChunkingStrategy:
    """Create semantic strategy using SentenceSplitter."""
    return SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def _recursive_split(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
    sep_idx: int = 0,
) -> list[str]:
    """Recursively split text using separators, preferring natural boundaries."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sep = separators[sep_idx] if sep_idx < len(separators) else ""
    if sep:
        parts = text.split(sep)
        chunks: list[str] = []
        current: list[str] = []

        def merge_len() -> int:
            return sum(len(p) for p in current) + (len(current) - 1) * len(sep) if current else 0

        for i, part in enumerate(parts):
            suffix = sep if i < len(parts) - 1 else ""
            candidate = part + suffix

            if len(candidate) > chunk_size:
                if current:
                    chunks.append(sep.join(current))
                    current = []
                sub_chunks = _recursive_split(candidate.strip(), chunk_size, chunk_overlap, separators, sep_idx + 1)
                chunks.extend(sub_chunks)
            elif merge_len() + len(candidate) <= chunk_size:
                current.append(part + (suffix if i < len(parts) - 1 else ""))
            else:
                if current:
                    chunks.append(sep.join(current))
                current = [part + suffix]

        if current:
            chunks.append(sep.join(current).rstrip(sep))
        return [c for c in chunks if c.strip()]
    else:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]


class RecursiveChunkingStrategy:
    """Recursive chunking: tries separators in order (paragraph, line, sentence, word)."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def get_nodes_from_documents(self, documents: list[Document]) -> list[BaseNode]:
        """Split documents using recursive separator-based chunking."""
        nodes = []
        for doc in documents:
            text = doc.text if hasattr(doc, "text") else str(doc.get_content())
            chunks = _recursive_split(text, self.chunk_size, self.chunk_overlap, RECURSIVE_SEPARATORS)
            for chunk_text in chunks:
                if chunk_text.strip():
                    nodes.append(TextNode(text=chunk_text, metadata=dict(doc.metadata) if doc.metadata else {}))
        return nodes


def _get_chunking_parser(strategy: str, chunk_size: int, chunk_overlap: int) -> ChunkingStrategy:
    """Factory for chunking strategies."""
    strategies = {
        "character": _create_character_strategy,
        "semantic": _create_semantic_strategy,
    }
    if strategy in strategies:
        return strategies[strategy](chunk_size, chunk_overlap)
    if strategy == "recursive":
        return RecursiveChunkingStrategy(chunk_size, chunk_overlap)
    raise ValueError(f"Unknown chunking strategy: {strategy}. Use: character, semantic, recursive")


@dataclass
class ChunkingResult:
    """Result from document chunking operations."""

    chunks: list[Document]
    file_name: str
    file_path: str
    file_size: int
    num_pages: int | None
    chunk_count: int
    chunking_params: dict[str, Any]
    file_hash: str
    # New fields for enhanced tracking
    pages_processed: int
    chunks_filtered: int
    text_cleaning_stats: dict[str, Any]


@dataclass
class ChunkMetadata:
    """Metadata for a single chunk."""

    chunk_index: int
    document_id: str
    document_name: str
    page_number: int | None  # Sequential page number (1-based)
    page_label: str | None  # PDF's internal page label
    source: str
    content_hash: str


def generate_content_hash(text: str) -> str:
    """Generate SHA-256 hash of text content.

    Handles Unicode surrogate characters by normalizing the text before encoding.
    """
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        normalized_text = text.encode("utf-8", errors="replace").decode("utf-8")
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    source_path: str | Path | None = None,
    enable_text_cleaning: bool = True,
    min_chunk_length: int = 10,
    progress_callback: Callable[[int, int], None] | None = None,
    strategy: str = "character",
) -> ChunkingResult:
    """Chunk a list of documents into smaller pieces with page-by-page processing.

    Supports multiple chunking strategies: character (default), semantic (sentence
    boundaries), recursive (paragraph/line/word boundaries). See CHUNKING.md.

    Args:
        documents: List of Document objects to chunk (typically one per page)
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        source_path: Optional source path for metadata
        enable_text_cleaning: Whether to apply text cleaning to chunks
        min_chunk_length: Minimum acceptable chunk length after cleaning
        progress_callback: Optional callback for page processing progress (page_num, total_pages)
        strategy: Chunking strategy: "character", "semantic", or "recursive"

    Returns:
        ChunkingResult with chunked documents and enhanced metadata
    """
    if not documents:
        return ChunkingResult(
            chunks=[],
            file_name="",
            file_path=str(source_path) if source_path else "",
            file_size=0,
            num_pages=None,
            chunk_count=0,
            chunking_params={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap, "strategy": strategy},
            file_hash="",
            pages_processed=0,
            chunks_filtered=0,
            text_cleaning_stats={},
        )

    logger.debug(
        "Starting document chunking",
        total_pages=len(documents),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy,
        enable_text_cleaning=enable_text_cleaning,
    )

    parser = _get_chunking_parser(strategy, chunk_size, chunk_overlap)

    # Calculate file information
    source_path = Path(source_path) if source_path else Path("unknown")
    file_size = source_path.stat().st_size if source_path.exists() else 0
    num_pages = len(documents) if documents else None

    # Process documents page by page for better progress tracking
    all_chunks = []
    chunks_filtered = 0
    text_cleaning_stats = {
        "total_chunks": 0,
        "cleaned_chunks": 0,
        "filtered_chunks": 0,
        "avg_chunk_length": 0,
        "avg_alphanumeric_ratio": 0.0,
    }

    for page_num, page_doc in enumerate(documents, 1):
        if progress_callback:
            progress_callback(page_num, len(documents))

        logger.debug("Processing page", page_num=page_num, total_pages=len(documents))

        page_chunks = parser.get_nodes_from_documents([page_doc])

        page_text = getattr(page_doc, "text", None) or (
            getattr(page_doc, "get_content", lambda: "")() if callable(getattr(page_doc, "get_content", None)) else ""
        )
        page_text = str(page_text or "")

        if not page_chunks and not (page_text or "").strip():
            empty_node = TextNode(
                text="",
                metadata=dict(page_doc.metadata) if hasattr(page_doc, "metadata") and page_doc.metadata else {},
            )
            empty_node.metadata["is_empty_page"] = True
            page_chunks = [empty_node]

        if enable_text_cleaning:
            cleaned_chunks = []
            for chunk in page_chunks:
                text_cleaning_stats["total_chunks"] += 1
                cleaned_text = clean_chunk_text(chunk.text, min_length=min_chunk_length)
                if cleaned_text is not None:
                    chunk.text = cleaned_text
                    cleaned_chunks.append(chunk)
                    text_cleaning_stats["cleaned_chunks"] += 1
                else:
                    chunk.text = ""
                    chunk.metadata["is_empty_page"] = True
                    cleaned_chunks.append(chunk)
                    text_cleaning_stats["cleaned_chunks"] += 1
                    chunks_filtered += 1
                    text_cleaning_stats["filtered_chunks"] += 1
            page_chunks = cleaned_chunks
        else:
            text_cleaning_stats["total_chunks"] += len(page_chunks)
            text_cleaning_stats["cleaned_chunks"] += len(page_chunks)

        for i, chunk in enumerate(page_chunks):
            doc_id = f"{source_path.stem}_{len(all_chunks) + i}"
            chunk.metadata.update(
                {
                    "chunk_index": len(all_chunks) + i,
                    "document_id": doc_id,
                    "document_name": source_path.name,
                    "page_number": page_num,
                    "page_label": str(page_num),
                    "source": str(source_path),
                    "content_hash": generate_content_hash(chunk.text),
                }
            )
        all_chunks.extend(page_chunks)

    if all_chunks:
        total_length = sum(len(chunk.text) for chunk in all_chunks)
        text_cleaning_stats["avg_chunk_length"] = total_length / len(all_chunks)
        total_alphanumeric_ratio = 0
        for chunk in all_chunks:
            stats = get_text_statistics(chunk.text)
            total_alphanumeric_ratio += stats["alphanumeric_ratio"]
        text_cleaning_stats["avg_alphanumeric_ratio"] = total_alphanumeric_ratio / len(all_chunks)

    combined_text = "\n".join(doc.text for doc in documents)
    file_hash = generate_content_hash(combined_text)

    logger.debug(
        "Document chunking completed",
        total_chunks=len(all_chunks),
        chunks_filtered=chunks_filtered,
        pages_processed=len(documents),
        avg_chunk_length=text_cleaning_stats.get("avg_chunk_length", 0),
    )

    return ChunkingResult(
        chunks=all_chunks,
        file_name=source_path.name,
        file_path=str(source_path),
        file_size=file_size,
        num_pages=num_pages,
        chunk_count=len(all_chunks),
        chunking_params={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap, "strategy": strategy},
        file_hash=file_hash,
        pages_processed=len(documents),
        chunks_filtered=chunks_filtered,
        text_cleaning_stats=text_cleaning_stats,
    )


def get_page_chunks(pdf_path: str | Path) -> dict[int, list[Document]]:
    """Get chunks organized by page number for analysis.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary mapping sequential page numbers to their chunks
    """
    from llama_index.readers.file import PDFReader

    pdf_path = Path(pdf_path)
    reader = PDFReader()
    documents = reader.load_data(pdf_path)

    result = chunk_documents(documents, source_path=pdf_path)

    page_chunks: dict[int, list[Document]] = {}
    for chunk in result.chunks:
        page_num = chunk.metadata.get("page_number")
        if page_num is not None:
            if page_num not in page_chunks:
                page_chunks[page_num] = []
            page_chunks[page_num].append(chunk)

    return page_chunks


__all__ = [
    "ChunkingResult",
    "ChunkMetadata",
    "ChunkingStrategy",
    "chunk_documents",
    "get_page_chunks",
    "generate_content_hash",
    "RecursiveChunkingStrategy",
]
