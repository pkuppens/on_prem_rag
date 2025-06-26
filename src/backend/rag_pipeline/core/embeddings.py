"""Embedding generation and vector storage for the RAG pipeline.

This module provides functionality for:
- Converting text chunks to embeddings using HuggingFace models
- Storing embeddings in ChromaDB vector store
- Querying embeddings for similarity search
- Centralized processing functions for all document types

Key features:
- HuggingFace embedding model integration
- ChromaDB vector storage with persistence
- Batch processing for efficiency
- Deduplication based on content hashes
- Comprehensive metadata preservation
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, TypedDict

from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import BaseNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from backend.rag_pipeline.config.vector_store import VectorStoreConfig
from backend.rag_pipeline.core.chunking import ChunkingResult, chunk_documents, generate_content_hash
from backend.rag_pipeline.core.document_loader import DocumentLoader
from backend.rag_pipeline.core.vector_store import ChromaVectorStoreManager
from backend.rag_pipeline.utils.embedding_model_utils import get_embedding_model
from backend.rag_pipeline.utils.progress import ProgressEvent, progress_notifier

from ..utils.logging import StructuredLogger

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingResult(TypedDict):
    """Result from a single embedding match."""

    text: str
    similarity_score: float
    document_id: str  # Unique identifier for the document
    document_name: str  # Name of the source document
    chunk_index: int  # Index of the chunk within the document
    record_id: str  # Database record ID
    page_number: str | int  # Page number from the source document


class QueryResult(TypedDict):
    """Result from querying embeddings."""

    primary_result: str
    all_results: list[EmbeddingResult]


__all__ = [
    "embed_text_nodes",
    "store_embeddings",
    "process_pdf",
    "chunk_pdf",
    "embed_chunks",
    "query_embeddings",
]


def embed_text_nodes(nodes: list[Document], model_name: str) -> list[list[float]]:
    """Convert text nodes to embeddings using HuggingFace models.

    Args:
        nodes: List of Document objects containing text to embed
        model_name: Name of the HuggingFace embedding model

    Returns:
        List of embedding vectors
    """
    logger.debug(f"Starting text embedding generation - model: {model_name}, nodes_to_embed: {len(nodes)}")

    embed_model = get_embedding_model(model_name)
    embeddings = []

    # Process each node to generate embeddings
    # This is typically the most time-consuming part of document processing
    for i, node in enumerate(nodes):
        logger.debug("Generating embedding for node", node_index=i, total_nodes=len(nodes), text_length=len(node.text))

        embedding = embed_model.get_text_embedding(node.text)
        embeddings.append(embedding)

    logger.debug("Text embedding generation completed", model=model_name, embeddings_generated=len(embeddings))

    return embeddings


def query_embeddings(
    query: str,
    model_name: str,
    persist_dir: str | Path,
    collection_name: str = "documents",
    top_k: int = 5,
) -> QueryResult:
    """Query embeddings for similar content.

    Args:
        query: The text query to search for
        model_name: Name of the HuggingFace embedding model
        persist_dir: Directory containing the vector store
        collection_name: Name of the collection to query
        top_k: Maximum number of results to return

    Returns:
        Dictionary containing query results with metadata
    """
    # Create embedding for the query
    embed_model = get_embedding_model(model_name)
    query_embedding = embed_model.get_text_embedding(query)

    # Query the vector store using proper config
    config = VectorStoreConfig(persist_directory=persist_dir, collection_name=collection_name)
    manager = ChromaVectorStoreManager(config)

    # Use the correct query method signature
    ids, distances = manager.query(query_embedding, top_k)

    # Get full results with metadata from the collection directly
    if ids:
        results = manager._collection.get(ids=ids, include=["documents", "metadatas"])

        formatted_results = []
        for i, doc_id in enumerate(ids):
            metadata = results["metadatas"][i] if results["metadatas"] and i < len(results["metadatas"]) else {}
            document_text = results["documents"][i] if results["documents"] and i < len(results["documents"]) else ""

            formatted_results.append(
                {
                    "text": document_text,
                    "similarity_score": 1 - distances[i],  # Convert distance to similarity
                    "document_id": metadata.get("document_id", "unknown"),
                    "document_name": metadata.get("document_name", "unknown"),
                    "chunk_index": metadata.get("chunk_index", "unknown"),
                    "record_id": doc_id,
                    "page_number": metadata.get("page_number", "unknown"),
                    "page_label": metadata.get("page_label", "unknown"),
                }
            )
    else:
        formatted_results = []

    # Set primary result to the first result's text, or empty if no results
    primary_result = formatted_results[0]["text"] if formatted_results else ""

    return {"primary_result": primary_result, "all_results": formatted_results}


def store_embeddings(
    ids: Iterable[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict] | None,
    persist_dir: str | Path,
    collection_name: str = "documents",
    deduplicate: bool = True,
) -> ChromaVectorStoreManager:
    """Store embeddings in the vector database.

    Args:
        ids: Unique identifiers for each embedding
        embeddings: List of embedding vectors
        metadatas: Metadata for each embedding
        persist_dir: Directory to store the vector database
        collection_name: Name of the collection
        deduplicate: Whether to deduplicate based on content hash

    Returns:
        ChromaVectorStoreManager instance
    """
    config = VectorStoreConfig(persist_directory=persist_dir, collection_name=collection_name)
    manager = ChromaVectorStoreManager(config)

    if deduplicate and metadatas:
        # Filter out duplicates based on content hash or text content
        unique_data = []
        seen_content = set()

        for i, metadata in enumerate(metadatas):
            # Try content_hash first, then fall back to text content
            content_hash = metadata.get("content_hash")
            if content_hash:
                content_key = content_hash
            else:
                # Use text content as fallback for deduplication
                content_key = metadata.get("text", f"id_{i}")

            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_data.append(i)

        # Keep only unique entries
        ids = [list(ids)[i] for i in unique_data]
        embeddings = [embeddings[i] for i in unique_data]
        metadatas = [metadatas[i] for i in unique_data]

    # Only add embeddings if we have data to add
    if ids and embeddings:
        # Extract documents from metadata if available
        documents = []
        if metadatas:
            for metadata in metadatas:
                # Use 'text' field from metadata as document content
                doc_text = metadata.get("text", "")
                documents.append(doc_text)
        else:
            documents = [""] * len(ids)

        # Add to collection with documents
        manager._collection.add(ids=list(ids), embeddings=list(embeddings), metadatas=metadatas, documents=documents)
    return manager


def process_document(
    file_path: str | Path,
    model_name: str,
    *,
    persist_dir: str | Path,
    collection_name: str = "documents",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    max_pages: int | None = None,
    deduplicate: bool = True,
    progress_callback: Callable[[str, float], None] | None = None,
) -> tuple[int, int]:
    """Process any document type and store embeddings.

    This is the centralized function for processing all document types (PDF, DOCX, TXT, MD).
    It combines document loading, chunking, and embedding for convenience.

    Args:
        file_path: Path to the document file
        model_name: Name of the HuggingFace embedding model
        persist_dir: Directory to store the embeddings
        collection_name: Name of the collection
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        max_pages: Maximum number of pages to process (None for all)
        deduplicate: Whether to deduplicate based on content hash
        progress_callback: Optional callback function for progress updates (0.0 to 1.0)
                          Should be a synchronous function

    Returns:
        Tuple of (number_of_chunks, number_of_stored_records)
    """
    file_path = Path(file_path)
    logger = StructuredLogger(__name__)

    # Progress tracking: Document loading (10% of total progress)
    logger.debug("Starting document processing", filename=file_path.name, model=model_name)
    if progress_callback:
        progress_callback(file_path.name, 0.0)  # 0% - Starting

    # Load the document
    logger.debug("Loading document", filename=file_path.name)
    document_loader = DocumentLoader()
    documents, document_metadata = document_loader.load_document(file_path)

    logger.debug(
        "Document loaded successfully",
        filename=file_path.name,
        pages=len(documents),
        file_size=document_metadata.file_size,
        file_type=document_metadata.file_type,
    )

    # Limit pages if requested (mainly for PDFs)
    if max_pages is not None and len(documents) > max_pages:
        documents = documents[:max_pages]
        logger.debug("Limited document pages", filename=file_path.name, max_pages=max_pages, actual_pages=len(documents))

    if progress_callback:
        progress_callback(file_path.name, 0.1)  # 10% - Document loaded

    # Progress tracking: Chunking (40% of total progress, from 10% to 50%)
    logger.debug(
        "Starting document chunking",
        filename=file_path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        total_pages=len(documents),
    )

    # Create a progress wrapper for chunking that maps page progress to overall progress
    def chunking_progress_wrapper(page_num: int, total_pages: int) -> None:
        """Map chunking progress (page_num/total_pages) to overall progress (10% to 50%)."""
        if progress_callback:
            # Map page progress from 0-1 to 10-50% range
            page_progress = page_num / total_pages
            overall_progress = 0.1 + (page_progress * 0.4)  # 10% to 50%
            progress_callback(file_path.name, overall_progress)

    # Chunk the documents using centralized chunking with page-by-page progress
    chunking_result = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        source_path=file_path,
        enable_text_cleaning=True,
        min_chunk_length=10,
        progress_callback=chunking_progress_wrapper,
    )

    logger.debug(
        "Document chunking completed",
        filename=file_path.name,
        chunks_created=chunking_result.chunk_count,
        chunks_filtered=chunking_result.chunks_filtered,
        pages_processed=chunking_result.pages_processed,
        avg_chunk_length=chunking_result.text_cleaning_stats.get("avg_chunk_length", 0),
        file_size=chunking_result.file_size,
    )

    if progress_callback:
        progress_callback(file_path.name, 0.5)  # 50% - Chunking completed

    # Progress tracking: Embedding and storage (50% of total progress, from 50% to 100%)
    logger.debug(
        "Starting embedding generation and storage",
        filename=file_path.name,
        chunks_to_process=len(chunking_result.chunks),
        model=model_name,
    )

    # Create a progress wrapper that maps 0.0-1.0 embedding progress to 0.5-1.0 total progress
    def embedding_progress_wrapper(embedding_progress: float) -> None:
        """Map embedding progress (0.0-1.0) to total progress (0.5-1.0)."""
        if progress_callback:
            # Map embedding progress from 0.0-1.0 to 0.5-1.0 range
            total_progress = 0.5 + (embedding_progress * 0.5)
            progress_callback(file_path.name, total_progress)

    # Create embeddings and store them
    chunks_processed, records_stored = embed_chunks(
        chunking_result,
        model_name,
        persist_dir=persist_dir,
        collection_name=collection_name,
        deduplicate=deduplicate,
        progress_callback=embedding_progress_wrapper,
    )

    logger.debug(
        "Document processing completed successfully",
        filename=file_path.name,
        chunks_processed=chunks_processed,
        records_stored=records_stored,
    )

    if progress_callback:
        progress_callback(file_path.name, 1.0)  # 100% - Processing completed

    return chunks_processed, records_stored


def process_pdf(
    pdf_path: str | Path,
    model_name: str,
    *,
    persist_dir: str | Path,
    collection_name: str = "documents",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    max_pages: int | None = None,
    deduplicate: bool = True,
) -> tuple[int, int]:
    """Process a PDF and store embeddings, returning counts.

    This function is a convenience wrapper around process_document specifically for PDFs.
    For new code, prefer using process_document() which handles all document types.
    """
    return process_document(
        pdf_path,
        model_name,
        persist_dir=persist_dir,
        collection_name=collection_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_pages=max_pages,
        deduplicate=deduplicate,
    )


def chunk_pdf(
    pdf_path: str | Path,
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    max_pages: int | None = None,
) -> ChunkingResult:
    """Chunk a PDF file into text chunks.

    Args:
        pdf_path: Path to the PDF file
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        max_pages: Maximum number of pages to process (None for all)

    Returns:
        ChunkingResult with chunked documents and metadata
    """
    pdf_path = Path(pdf_path)

    # Load the document
    print(f"Loading PDF document: {pdf_path.name}")
    document_loader = DocumentLoader()
    documents, document_metadata = document_loader.load_document(pdf_path)

    print(f"Loaded {len(documents)} pages from PDF")

    # Limit pages if requested
    if max_pages is not None:
        documents = documents[:max_pages]
        print(f"Limited to first {len(documents)} pages")

    # Chunk the documents using centralized chunking
    print(f"Chunking documents with size={chunk_size}, overlap={chunk_overlap}")
    chunking_result = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        source_path=pdf_path,
    )

    print(f"Created {chunking_result.chunk_count} chunks")
    return chunking_result


def create_clean_metadata(node, file_path: Path, chunk_index: int) -> dict:
    """Create clean, serializable metadata for a chunk.

    This function extracts only serializable metadata fields and omits
    problematic LlamaIndex objects like RelatedNodeInfo that cause JSON
    serialization errors.

    Args:
        node: LlamaIndex node object
        file_path: Path to the source document
        chunk_index: Index of this chunk within the document

    Returns:
        Clean metadata dictionary with only serializable fields
    """
    # Generate a stable document ID from the file path and chunk index
    doc_id = f"{file_path.stem}_{chunk_index}"

    # Extract only serializable metadata fields
    clean_metadata = {
        "text": node.text,
        "document_name": file_path.name,
        "document_id": doc_id,
        "chunk_index": chunk_index,
        "source": str(file_path),
    }

    # Safely extract metadata fields, only including serializable ones
    if hasattr(node, "metadata") and node.metadata:
        # Only include basic types that are JSON serializable
        for key, value in node.metadata.items():
            # Skip non-serializable objects like RelatedNodeInfo
            if isinstance(value, str | int | float | bool | list | dict) and not key.startswith("_"):
                # For lists and dicts, ensure they only contain serializable items
                if isinstance(value, list):
                    # Only include lists of basic types
                    if all(isinstance(item, str | int | float | bool) for item in value):
                        clean_metadata[key] = value
                elif isinstance(value, dict):
                    # Only include dicts with basic type values
                    if all(isinstance(v, str | int | float | bool | list) for v in value.values()):
                        clean_metadata[key] = value
                else:
                    clean_metadata[key] = value

    # Ensure we have the essential fields with defaults
    clean_metadata.setdefault("page_number", "unknown")
    clean_metadata.setdefault("page_label", "unknown")
    clean_metadata.setdefault("content_hash", "")

    return clean_metadata


def embed_chunks(
    chunking_result: ChunkingResult,
    model_name: str,
    *,
    persist_dir: str | Path,
    collection_name: str = "documents",
    deduplicate: bool = True,
    progress_callback: Callable[[float], None] | None = None,
) -> tuple[int, int]:
    """Embed chunks and store them in a vector database.

    Args:
        chunking_result: Result from chunk_pdf function or chunk_documents
        model_name: Name of the HuggingFace embedding model
        persist_dir: Directory to store the embeddings
        collection_name: Name of the collection
        deduplicate: Whether to deduplicate based on content hash
        progress_callback: Optional callback function for progress updates (0.0 to 1.0)
                          Should be a synchronous function

    Returns:
        Tuple of (number_of_chunks, number_of_stored_records)
    """
    nodes = chunking_result.chunks
    file_path = Path(chunking_result.file_path)
    logger = StructuredLogger(__name__)

    # Filter out empty pages before embedding
    non_empty_nodes = []
    empty_pages_skipped = 0

    for node in nodes:
        # Check if this is an empty page that should be skipped during embedding
        if hasattr(node, "metadata") and node.metadata and node.metadata.get("is_empty_page", False):
            empty_pages_skipped += 1
            logger.debug(
                "Skipping empty page during embedding",
                page_number=node.metadata.get("page_number", "unknown"),
                chunk_index=node.metadata.get("chunk_index", "unknown"),
            )
        else:
            non_empty_nodes.append(node)

    if empty_pages_skipped > 0:
        logger.info(
            f"Skipped {empty_pages_skipped} empty pages during embedding",
            filename=file_path.name,
            total_chunks=len(nodes),
            non_empty_chunks=len(non_empty_nodes),
        )

    # Progress tracking: Embedding generation (60% of embedding phase, from 50% to 80% of total)
    logger.debug("Starting embedding generation", filename=file_path.name, chunks_to_embed=len(non_empty_nodes), model=model_name)

    # Log first node for debugging (but don't log the full metadata to avoid serialization issues)
    if non_empty_nodes:
        logger.debug(
            "First node info",
            filename=file_path.name,
            node_text_length=len(non_empty_nodes[0].text),
            has_metadata=hasattr(non_empty_nodes[0], "metadata") and non_empty_nodes[0].metadata is not None,
        )

    # Generate embeddings - this is the most time-consuming part
    logger.debug("Generating embeddings for chunks", filename=file_path.name, total_chunks=len(non_empty_nodes))
    embeddings = embed_text_nodes(non_empty_nodes, model_name)

    logger.debug("Embedding generation completed", filename=file_path.name, embeddings_generated=len(embeddings))

    if progress_callback:
        progress_callback(0.8)  # 80% of total progress - Embeddings generated

    # Progress tracking: Metadata preparation and storage (20% of embedding phase, from 80% to 100% of total)
    logger.debug("Preparing clean metadata for storage", filename=file_path.name)

    # Create clean, serializable metadata for each chunk
    metadatas = []
    for i, node in enumerate(non_empty_nodes):
        clean_metadata = create_clean_metadata(node, file_path, i)
        metadatas.append(clean_metadata)

    logger.debug(
        "Clean metadata preparation completed",
        filename=file_path.name,
        metadata_entries=len(metadatas),
        sample_metadata_keys=list(metadatas[0].keys()) if metadatas else [],
    )

    # Progress tracking: Vector database storage (final 20% of embedding phase)
    logger.debug(
        "Storing embeddings in vector database",
        filename=file_path.name,
        embeddings_to_store=len(embeddings),
        collection=collection_name,
    )

    manager = store_embeddings(
        [f"{file_path.stem}_{i}" for i in range(len(non_empty_nodes))],  # Generate stable IDs
        embeddings,
        metadatas,
        persist_dir,
        collection_name,
        deduplicate=deduplicate,
    )

    count = manager._collection.count()
    logger.debug("Vector database storage completed", filename=file_path.name, records_stored=count, collection=collection_name)

    if progress_callback:
        progress_callback(1.0)  # 100% of total progress - Storage completed

    return len(nodes), count  # Return original chunk count for consistency
