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
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser

logger = logging.getLogger(__name__)


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


@dataclass
class ChunkMetadata:
    """Metadata for a single chunk."""

    chunk_index: int
    document_id: str
    document_name: str
    page_number: int | None  # Sequential page number (1-based)
    page_label: str | None   # PDF's internal page label
    source: str
    content_hash: str


def generate_content_hash(text: str) -> str:
    """Generate a hash of the text content for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    source_path: str | Path | None = None,
) -> ChunkingResult:
    """Chunk a list of documents into smaller pieces.

    Uses SimpleNodeParser with character-based chunking strategy.
    See docs/technical/CHUNKING.md#implementation-details for configuration rationale.

    Args:
        documents: List of Document objects to chunk
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        source_path: Optional source path for metadata

    Returns:
        ChunkingResult with chunked documents and metadata
        
    Note:
        This is the centralized chunking function that should be used for all document types.
        It properly handles both page labels and sequential page numbers for PDFs.
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
        )

    # Set up the node parser for chunking
    parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Process the documents
    chunks = parser.get_nodes_from_documents(documents)

    # Calculate file information
    source_path = Path(source_path) if source_path else Path("unknown")
    file_size = source_path.stat().st_size if source_path.exists() else 0
    num_pages = len(documents) if documents else None

    # Generate file hash for deduplication
    combined_text = "\n".join(doc.text for doc in documents)
    file_hash = generate_content_hash(combined_text)

    # Create page mapping for sequential page numbers vs page labels
    # Map document IDs to page information
    page_mapping = {}
    for i, doc in enumerate(documents):
        sequential_page = i + 1  # 1-based sequential page number
        page_label = doc.metadata.get("page_label", str(sequential_page))
        page_mapping[doc.doc_id] = {
            "sequential_page": sequential_page,
            "page_label": page_label
        }

    # Enhanced metadata for chunks
    for i, chunk in enumerate(chunks):
        # Generate a stable document ID from the file path and chunk index
        doc_id = f"{source_path.stem}_{i}"
        
        # Get the source document for this chunk to extract page information
        source_doc_id = chunk.ref_doc_id if hasattr(chunk, 'ref_doc_id') else None
        page_info = page_mapping.get(source_doc_id, {
            "sequential_page": None,
            "page_label": "unknown"
        })

        # Ensure we have valid page information - fallback to extracting from existing metadata
        if page_info["sequential_page"] is None and "page_label" in chunk.metadata:
            # Try to extract page number from existing page_label if available
            existing_page_label = chunk.metadata.get("page_label", "unknown")
            if existing_page_label != "unknown":
                try:
                    # If page_label is a number, use it as both page_number and page_label
                    if isinstance(existing_page_label, (int, str)) and str(existing_page_label).isdigit():
                        page_info = {
                            "sequential_page": int(existing_page_label),
                            "page_label": existing_page_label
                        }
                    else:
                        page_info = {
                            "sequential_page": None,
                            "page_label": existing_page_label
                        }
                except (ValueError, TypeError):
                    pass

        # Update chunk metadata with both sequential page number and page label
        chunk.metadata.update(
            {
                "chunk_index": i,
                "document_id": doc_id,
                "document_name": source_path.name,
                "page_number": page_info["sequential_page"],  # Sequential page number for navigation
                "page_label": page_info["page_label"],        # PDF's internal page label for display
                "source": str(source_path),
                "content_hash": generate_content_hash(chunk.text),
            }
        )

    return ChunkingResult(
        chunks=chunks,
        file_name=source_path.name,
        file_path=str(source_path),
        file_size=file_size,
        num_pages=num_pages,
        chunk_count=len(chunks),
        chunking_params={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
        file_hash=file_hash,
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
