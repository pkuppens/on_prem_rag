"""Chunking infrastructure — text-to-chunk strategies.

This module adapts LlamaIndex node parsers to produce domain ``Chunk`` objects.
The LlamaIndex dependency is isolated here; application code works with domain
``Chunk`` and ``IngestionDocument`` types only.

Supported strategies: character, semantic, recursive.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode

from backend.ingestion.domain.value_objects import Chunk, IngestionDocument
from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.rag_pipeline.utils.text_cleaning import clean_chunk_text, get_text_statistics

logger = StructuredLogger(__name__)

# Separators for recursive chunking: try paragraph, line, then word boundaries.
RECURSIVE_SEPARATORS = ["\n\n", "\n", ". ", " "]


def generate_content_hash(text: str) -> str:
    """Generate SHA-256 hash of text content.

    Handles Unicode surrogate characters by normalizing the text before encoding.
    """
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        normalized_text = text.encode("utf-8", errors="replace").decode("utf-8")
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def _to_llama_document(doc: IngestionDocument) -> LlamaDocument:
    """Convert a domain ``IngestionDocument`` to a LlamaIndex ``Document``.

    This is the inverse of the conversion in document_loader.py. Chunking
    strategies work with LlamaIndex types internally but we convert back
    to domain ``Chunk`` objects at the boundary.
    """
    return LlamaDocument(text=doc.text, metadata=dict(doc.metadata))


# ---------------------------------------------------------------------------
# Chunking strategy implementations (internal — use LlamaIndex parsers)
# ---------------------------------------------------------------------------


def _create_character_strategy(chunk_size: int, chunk_overlap: int) -> Any:
    """Create character-based strategy using RecursiveChunkingStrategy."""
    return RecursiveChunkingStrategy(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def _create_semantic_strategy(chunk_size: int, chunk_overlap: int) -> Any:
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

    def get_nodes_from_documents(self, documents: list[LlamaDocument]) -> list[BaseNode]:
        """Split documents using recursive separator-based chunking."""
        nodes = []
        for doc in documents:
            text = doc.text if hasattr(doc, "text") else str(doc.get_content())
            chunks = _recursive_split(text, self.chunk_size, self.chunk_overlap, RECURSIVE_SEPARATORS)
            for chunk_text in chunks:
                if chunk_text.strip():
                    nodes.append(TextNode(text=chunk_text, metadata=dict(doc.metadata) if doc.metadata else {}))
        return nodes


def _get_chunking_parser(strategy: str, chunk_size: int, chunk_overlap: int) -> Any:
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


# ---------------------------------------------------------------------------
# Public chunking function — converts LlamaIndex nodes back to domain Chunks
# ---------------------------------------------------------------------------


def chunk_documents(
    documents: list[IngestionDocument],
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    source_path: str | Path | None = None,
    enable_text_cleaning: bool = True,
    min_chunk_length: int = 10,
    progress_callback: Callable[[int, int], None] | None = None,
    strategy: str = "character",
) -> list[Chunk]:
    """Chunk domain documents into domain ``Chunk`` objects.

    Internally converts to LlamaIndex types for parsing, then converts
    back to domain ``Chunk`` objects at the boundary.

    Args:
        documents: List of IngestionDocument to chunk (typically one per page).
        chunk_size: Maximum size of each chunk in characters.
        chunk_overlap: Number of characters to overlap between chunks.
        source_path: Optional source path for metadata.
        enable_text_cleaning: Whether to apply text cleaning.
        min_chunk_length: Minimum acceptable chunk length after cleaning.
        progress_callback: Optional callback(page_num, total_pages).
        strategy: Chunking strategy: "character", "semantic", or "recursive".

    Returns:
        List of domain ``Chunk`` objects.
    """
    if not documents:
        return []

    logger.debug(
        "Starting document chunking",
        total_pages=len(documents),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy,
        enable_text_cleaning=enable_text_cleaning,
    )

    parser = _get_chunking_parser(strategy, chunk_size, chunk_overlap)

    source_path = Path(source_path) if source_path else Path("unknown")

    all_chunks: list[Chunk] = []
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

        # Convert to LlamaIndex Document for internal parsing
        li_doc = _to_llama_document(page_doc)
        page_chunks: list[BaseNode] = parser.get_nodes_from_documents([li_doc])

        # Preserve empty pages
        page_text = page_doc.text or ""
        if not page_chunks and not page_text.strip():
            empty_node = TextNode(text="", metadata=dict(page_doc.metadata) if page_doc.metadata else {})
            empty_node.metadata["is_empty_page"] = True
            page_chunks = [empty_node]

        # Clean and filter chunks
        if enable_text_cleaning:
            cleaned_nodes: list[BaseNode] = []
            for chunk in page_chunks:
                text_cleaning_stats["total_chunks"] += 1
                cleaned_text = clean_chunk_text(chunk.text, min_length=min_chunk_length)
                if cleaned_text is not None:
                    chunk.text = cleaned_text
                    cleaned_nodes.append(chunk)
                    text_cleaning_stats["cleaned_chunks"] += 1
                else:
                    chunk.text = ""
                    chunk.metadata["is_empty_page"] = True
                    cleaned_nodes.append(chunk)
                    text_cleaning_stats["cleaned_chunks"] += 1
                    chunks_filtered += 1
                    text_cleaning_stats["filtered_chunks"] += 1
            page_chunks = cleaned_nodes
        else:
            text_cleaning_stats["total_chunks"] += len(page_chunks)
            text_cleaning_stats["cleaned_chunks"] += len(page_chunks)

        # Convert nodes to domain Chunks
        for node in page_chunks:
            chunk_index = len(all_chunks)
            doc_id = f"{source_path.stem}_{chunk_index}"
            domain_chunk = Chunk(
                text=node.text or "",
                chunk_index=chunk_index,
                document_id=doc_id,
                document_name=source_path.name,
                page_number=page_num,
                page_label=str(page_num),
                source=str(source_path),
                content_hash=generate_content_hash(node.text or ""),
                is_empty=node.metadata.get("is_empty_page", False),
                metadata={
                    "chunk_index": chunk_index,
                    "document_id": doc_id,
                    "document_name": source_path.name,
                    "page_number": page_num,
                    "page_label": str(page_num),
                    "source": str(source_path),
                    "content_hash": generate_content_hash(node.text or ""),
                    **{k: v for k, v in node.metadata.items() if isinstance(v, str | int | float | bool)},
                },
            )
            all_chunks.append(domain_chunk)

        logger.debug(
            "Page processed",
            page_num=page_num,
            chunks_created=len(page_chunks),
            total_chunks_so_far=len(all_chunks),
        )

    # Calculate stats
    if all_chunks:
        total_length = sum(len(c.text) for c in all_chunks)
        text_cleaning_stats["avg_chunk_length"] = total_length / len(all_chunks)
        total_alphanumeric_ratio = 0
        for c in all_chunks:
            stats = get_text_statistics(c.text)
            total_alphanumeric_ratio += stats["alphanumeric_ratio"]
        text_cleaning_stats["avg_alphanumeric_ratio"] = total_alphanumeric_ratio / len(all_chunks)

    logger.debug(
        "Document chunking completed",
        total_chunks=len(all_chunks),
        chunks_filtered=chunks_filtered,
        pages_processed=len(documents),
        avg_chunk_length=text_cleaning_stats.get("avg_chunk_length", 0),
    )

    return all_chunks
