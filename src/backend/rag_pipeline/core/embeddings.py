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

import hashlib
import logging
from pathlib import Path
from typing import Any, Iterable, Sequence, TypedDict

from llama_index.core import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from backend.rag_pipeline.config.vector_store import VectorStoreConfig
from backend.rag_pipeline.core.chunking import ChunkingResult, chunk_documents, generate_content_hash
from backend.rag_pipeline.core.document_loader import DocumentLoader
from backend.rag_pipeline.core.vector_store import ChromaVectorStoreManager

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
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    embeddings = []

    for node in nodes:
        embedding = embed_model.get_text_embedding(node.text)
        embeddings.append(embedding)

    return embeddings


def query_embeddings(
    query: str,
    model_name: str,
    persist_dir: str | Path,
    collection_name: str = "documents",
    top_k: int = 5,
) -> dict[str, Any]:
    """Query the vector store for similar embeddings.

    Args:
        query: Query text
        model_name: Name of the HuggingFace embedding model
        persist_dir: Directory containing the vector store
        collection_name: Name of the collection to query
        top_k: Number of results to return

    Returns:
        Dictionary containing query results with metadata
    """
    # Create embedding for the query
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    query_embedding = embed_model.get_text_embedding(query)

    # Query the vector store
    manager = ChromaVectorStoreManager(persist_dir=str(persist_dir), collection_name=collection_name)
    results = manager.query(query_embeddings=[query_embedding], n_results=top_k)

    # Format results for API response
    formatted_results = []
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            
            formatted_results.append(
                {
                    "text": results["documents"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "document_id": metadata.get("document_id", "unknown"),
                    "document_name": metadata.get("document_name", "unknown"),
                    "chunk_index": metadata.get("chunk_index", "unknown"),
                    "record_id": results["ids"][0][i],
                    "page_number": metadata.get("page_number", "unknown"),
                    "page_label": metadata.get("page_label", "unknown"),
                }
            )

    return {"results": formatted_results, "query": query, "total_results": len(formatted_results)}


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
    manager = ChromaVectorStoreManager(persist_dir=str(persist_dir), collection_name=collection_name)

    if deduplicate and metadatas:
        # Filter out duplicates based on content hash
        unique_data = []
        seen_hashes = set()

        for i, metadata in enumerate(metadatas):
            content_hash = metadata.get("content_hash")
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_data.append(i)
        
        # Keep only unique entries
        ids = [list(ids)[i] for i in unique_data]
        embeddings = [embeddings[i] for i in unique_data]
        metadatas = [metadatas[i] for i in unique_data]

    manager.add_embeddings(ids=ids, embeddings=embeddings, metadatas=metadatas)
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

    Returns:
        Tuple of (number_of_chunks, number_of_stored_records)
    """
    file_path = Path(file_path)

    # Load the document
    document_loader = DocumentLoader()
    documents, document_metadata = document_loader.load_document(file_path)

    # Limit pages if requested (mainly for PDFs)
    if max_pages is not None and len(documents) > max_pages:
        documents = documents[:max_pages]

    # Chunk the documents using centralized chunking
    chunking_result = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        source_path=file_path,
    )

    # Create embeddings and store them
    chunks_processed, records_stored = embed_chunks(
        chunking_result,
        model_name,
        persist_dir=persist_dir,
        collection_name=collection_name,
        deduplicate=deduplicate,
    )

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


def embed_chunks(
    chunking_result: ChunkingResult,
    model_name: str,
    *,
    persist_dir: str | Path,
    collection_name: str = "documents",
    deduplicate: bool = True,
) -> tuple[int, int]:
    """Embed chunks and store them in a vector database.

    Args:
        chunking_result: Result from chunk_pdf function or chunk_documents
        model_name: Name of the HuggingFace embedding model
        persist_dir: Directory to store the embeddings
        collection_name: Name of the collection
        deduplicate: Whether to deduplicate based on content hash

    Returns:
        Tuple of (number_of_chunks, number_of_stored_records)
    """
    nodes = chunking_result.chunks
    file_path = Path(chunking_result.file_path)

    # Log first node for debugging
    if nodes:
        logger.debug(f"First node attributes: {vars(nodes[0])}")
        logger.debug(f"First node metadata: {nodes[0].metadata}")

    # Generate embeddings with progress reporting
    print(f"Generating embeddings for {len(nodes)} chunks...")
    embeddings = embed_text_nodes(nodes, model_name)

    # Enhanced metadata with document information
    metadatas = []
    for i, node in enumerate(nodes):
        # Generate a stable document ID from the file path and chunk index
        doc_id = f"{file_path.stem}_{i}"

        metadatas.append(
            {
                "text": node.text,
                "document_name": file_path.name,
                "document_id": doc_id,
                "chunk_index": i,
                "page_number": node.metadata.get("page_number", "unknown"),
                "page_label": node.metadata.get("page_label", "unknown"),
                "source": str(file_path),
                "content_hash": node.metadata.get("content_hash", ""),
            }
        )

    print(f"Storing {len(embeddings)} embeddings...")
    manager = store_embeddings(
        [f"{file_path.stem}_{i}" for i in range(len(nodes))],  # Generate stable IDs
        embeddings,
        metadatas,
        persist_dir,
        collection_name,
        deduplicate=deduplicate,
    )
    count = manager._collection.count()
    print(f"Stored {count} records in vector database")
    return len(nodes), count
