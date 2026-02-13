"""Document chunking functionality for the RAG pipeline.

This module handles the chunking of documents loaded by the document loader.
It provides functionality to split documents into smaller pieces suitable for
embedding and retrieval.

See docs/technical/CHUNKING.md for detailed chunking strategies, implementation
decisions, and performance considerations.

Key features:
- Page-based chunking with token size considerations
- Chunk overlap management
- Metadata preservation including both page labels and sequential page numbers
- Support for different chunking strategies
- Text cleaning and quality validation
- Progress reporting for page-by-page processing
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser

from ..utils.logging import StructuredLogger
from ..utils.text_cleaning import clean_chunk_text, get_text_statistics

logger = StructuredLogger(__name__)


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
    # Normalize Unicode characters and handle surrogates
    try:
        # First try direct encoding
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        # If that fails, normalize and try again
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
) -> ChunkingResult:
    """Chunk a list of documents into smaller pieces with page-by-page processing.

    Uses SimpleNodeParser with character-based chunking strategy and optional text cleaning.
    See docs/technical/CHUNKING.md#implementation-details for configuration rationale.

    Args:
        documents: List of Document objects to chunk (typically one per page)
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        source_path: Optional source path for metadata
        enable_text_cleaning: Whether to apply text cleaning to chunks
        min_chunk_length: Minimum acceptable chunk length after cleaning
        progress_callback: Optional callback for page processing progress (page_num, total_pages)

    Returns:
        ChunkingResult with chunked documents and enhanced metadata

    Note:
        This is the centralized chunking function that should be used for all document types.
        It properly handles both page labels and sequential page numbers for PDFs.
        Text cleaning is applied to improve chunk quality and remove problematic content.
    """
    if not documents:
        return ChunkingResult(
            chunks=[],
            file_name="",
            file_path=str(source_path) if source_path else "",
            file_size=0,
            num_pages=None,
            chunk_count=0,
            chunking_params={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
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
        enable_text_cleaning=enable_text_cleaning,
    )

    # Set up the node parser for chunking
    parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

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
        # Notify progress for this page
        if progress_callback:
            progress_callback(page_num, len(documents))

        logger.debug("Processing page", page_num=page_num, total_pages=len(documents))

        # Chunk this page
        page_chunks = parser.get_nodes_from_documents([page_doc])

        # Clean and filter chunks if enabled
        if enable_text_cleaning:
            cleaned_chunks = []
            for chunk in page_chunks:
                text_cleaning_stats["total_chunks"] += 1

                # Clean the chunk text
                cleaned_text = clean_chunk_text(chunk.text, min_length=min_chunk_length)

                if cleaned_text is not None:
                    # Update chunk with cleaned text
                    chunk.text = cleaned_text
                    cleaned_chunks.append(chunk)
                    text_cleaning_stats["cleaned_chunks"] += 1
                else:
                    # Keep empty chunks for page numbering consistency, but mark them as empty
                    chunk.text = ""  # Empty text
                    chunk.metadata["is_empty_page"] = True  # Mark as empty for embedding skip
                    cleaned_chunks.append(chunk)
                    text_cleaning_stats["cleaned_chunks"] += 1
                    chunks_filtered += 1
                    text_cleaning_stats["filtered_chunks"] += 1
                    logger.debug("Marked empty page", page_num=page_num, original_length=len(chunk.text))

            page_chunks = cleaned_chunks
        else:
            # Count chunks even without cleaning
            text_cleaning_stats["total_chunks"] += len(page_chunks)
            text_cleaning_stats["cleaned_chunks"] += len(page_chunks)

        # Add page-specific metadata to chunks
        for i, chunk in enumerate(page_chunks):
            # Generate a stable document ID from the file path and chunk index
            doc_id = f"{source_path.stem}_{len(all_chunks) + i}"

            # Update chunk metadata with page information
            chunk.metadata.update(
                {
                    "chunk_index": len(all_chunks) + i,
                    "document_id": doc_id,
                    "document_name": source_path.name,
                    "page_number": page_num,  # Sequential page number for navigation
                    "page_label": str(page_num),  # PDF's internal page label for display
                    "source": str(source_path),
                    "content_hash": generate_content_hash(chunk.text),
                }
            )

        all_chunks.extend(page_chunks)
        logger.debug("Page processed", page_num=page_num, chunks_created=len(page_chunks), total_chunks_so_far=len(all_chunks))

    # Calculate text cleaning statistics
    if all_chunks:
        total_length = sum(len(chunk.text) for chunk in all_chunks)
        text_cleaning_stats["avg_chunk_length"] = total_length / len(all_chunks)

        # Calculate average alphanumeric ratio
        total_alphanumeric_ratio = 0
        for chunk in all_chunks:
            stats = get_text_statistics(chunk.text)
            total_alphanumeric_ratio += stats["alphanumeric_ratio"]
        text_cleaning_stats["avg_alphanumeric_ratio"] = total_alphanumeric_ratio / len(all_chunks)

    # Generate file hash for deduplication
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
        chunking_params={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
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

    Note:
        This function loads the PDF and chunks it with default parameters
        for analysis purposes. Use chunk_documents() for production chunking.
        Page numbers are 1-based sequential indices, not PDF page labels.
    """
    from llama_index.readers.file import PDFReader

    pdf_path = Path(pdf_path)
    reader = PDFReader()
    documents = reader.load_data(pdf_path)

    # Chunk the documents
    result = chunk_documents(documents, source_path=pdf_path)

    # Organize chunks by sequential page number
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
    "chunk_documents",
    "get_page_chunks",
    "generate_content_hash",
]
