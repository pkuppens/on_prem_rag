"""Utility functions for embedding documents and storing embeddings."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TypedDict

from llama_index.core import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from rag_pipeline.config.vector_store import VectorStoreConfig
from rag_pipeline.core.chunking import ChunkingResult, chunk_documents, generate_content_hash
from rag_pipeline.core.document_loader import DocumentLoader
from rag_pipeline.core.vector_store import ChromaVectorStoreManager

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
    """Embed text nodes using a HuggingFace model."""
    embed_model = HuggingFaceEmbedding(model_name=model_name)

    embeddings = []
    total_nodes = len(nodes)

    for i, node in enumerate(nodes, 1):
        if i % 10 == 0 or i == total_nodes:  # Report progress every 10 embeddings or at the end
            print(f"  Embedding progress: {i}/{total_nodes} chunks ({i / total_nodes:.1%})")

        embedding = embed_model.get_text_embedding(node.text)
        embeddings.append(embedding)

    return embeddings


# Content hash function moved to chunking.py module


def store_embeddings(
    ids: Iterable[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict] | None,
    persist_dir: str | Path,
    collection_name: str = "documents",
    deduplicate: bool = True,
) -> ChromaVectorStoreManager:
    """Store embeddings in a Chroma vector store.

    Args:
        ids: List of unique identifiers for the embeddings
        embeddings: List of embedding vectors
        metadatas: List of metadata dictionaries
        persist_dir: Directory to store the embeddings
        collection_name: Name of the collection
        deduplicate: Whether to deduplicate based on content hash
    """
    # Convert persist_dir to Path if it's a string
    persist_dir = Path(persist_dir) if isinstance(persist_dir, str) else persist_dir
    # Ensure the directory exists
    persist_dir.mkdir(parents=True, exist_ok=True)
    config = VectorStoreConfig(host=None, persist_directory=persist_dir, collection_name=collection_name)
    manager = ChromaVectorStoreManager(config)

    if deduplicate and metadatas:
        # Get existing content hashes
        existing_hashes = set()
        if manager._collection.count() > 0:
            existing = manager._collection.get()
            existing_hashes = {m.get("content_hash", "") for m in existing["metadatas"]}

        # Filter out duplicates
        filtered_data = []
        for id_, emb, meta in zip(ids, embeddings, metadatas, strict=False):
            content_hash = generate_content_hash(meta["text"])
            if content_hash not in existing_hashes:
                meta["content_hash"] = content_hash
                filtered_data.append((id_, emb, meta))
                existing_hashes.add(content_hash)

        if filtered_data:
            manager.add_embeddings(
                ids=[d[0] for d in filtered_data],
                embeddings=[d[1] for d in filtered_data],
                metadatas=[d[2] for d in filtered_data],
            )
    else:
        manager.add_embeddings(
            ids=list(ids),
            embeddings=[list(e) for e in embeddings],
            metadatas=list(metadatas) if metadatas else None,
        )

    return manager


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

    This function combines document loading, chunking, and embedding
    for convenience. For more control, use the separate functions.
    """
    pdf_path = Path(pdf_path)

    # Load the document
    document_loader = DocumentLoader()
    documents, document_metadata = document_loader.load_document(pdf_path)

    # Limit pages if requested
    if max_pages is not None:
        documents = documents[:max_pages]

    # Chunk the documents
    chunking_result = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        source_path=pdf_path,
    )

    nodes = chunking_result.chunks

    # Log first node for debugging
    if nodes:
        logger.debug(f"First node attributes: {vars(nodes[0])}")
        logger.debug(f"First node metadata: {nodes[0].metadata}")

    embeddings = embed_text_nodes(nodes, model_name)

    # Enhanced metadata with document information
    metadatas = []
    for i, node in enumerate(nodes):
        # Generate a stable document ID from the file path and chunk index
        doc_id = f"{pdf_path.stem}_{i}"

        metadatas.append(
            {
                "text": node.text,
                "document_name": pdf_path.name,
                "document_id": doc_id,
                "chunk_index": i,
                "page_number": node.metadata.get("page_label", "unknown"),
                "source": str(pdf_path),
            }
        )

    manager = store_embeddings(
        [f"{pdf_path.stem}_{i}" for i in range(len(nodes))],  # Generate stable IDs
        embeddings,
        metadatas,
        persist_dir,
        collection_name,
        deduplicate=deduplicate,
    )
    count = manager._collection.count()
    return len(nodes), count


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

    # Chunk the documents
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
        chunking_result: Result from chunk_pdf function
        model_name: Name of the HuggingFace embedding model
        persist_dir: Directory to store the embeddings
        collection_name: Name of the collection
        deduplicate: Whether to deduplicate based on content hash

    Returns:
        Tuple of (number_of_chunks, number_of_stored_records)
    """
    nodes = chunking_result.chunks
    pdf_path = Path(chunking_result.file_path)

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
        doc_id = f"{pdf_path.stem}_{i}"

        metadatas.append(
            {
                "text": node.text,
                "document_name": pdf_path.name,
                "document_id": doc_id,
                "chunk_index": i,
                "page_number": node.metadata.get("page_label", "unknown"),
                "source": str(pdf_path),
            }
        )

    print(f"Storing {len(embeddings)} embeddings...")
    manager = store_embeddings(
        [f"{pdf_path.stem}_{i}" for i in range(len(nodes))],  # Generate stable IDs
        embeddings,
        metadatas,
        persist_dir,
        collection_name,
        deduplicate=deduplicate,
    )
    count = manager._collection.count()
    print(f"Stored {count} records in vector database")
    return len(nodes), count


def query_embeddings(
    query: str,
    model_name: str,
    *,
    persist_dir: str | Path,
    collection_name: str = "documents",
    top_k: int = 3,
) -> QueryResult:
    """Query the persisted embeddings and return texts with similarity scores.

    Args:
        query: The text to search for
        model_name: Name of the HuggingFace embedding model to use
        persist_dir: Directory where embeddings are stored
        collection_name: Name of the collection to search in
        top_k: Number of results to return

    Returns:
        A QueryResult containing:
        - primary_result: The text of the most similar embedding
        - all_results: List of all matching results with their similarity scores

    Note:
        Similarity scores are cosine similarities, ranging from -1 to 1.
        Higher scores (closer to 1) indicate more similar embeddings.
    """
    # Convert persist_dir to Path if it's a string
    persist_dir = Path(persist_dir) if isinstance(persist_dir, str) else persist_dir
    # Ensure the directory exists
    persist_dir.mkdir(parents=True, exist_ok=True)
    config = VectorStoreConfig(host=None, persist_directory=persist_dir, collection_name=collection_name)
    manager = ChromaVectorStoreManager(config)
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    q_emb = embed_model.get_query_embedding(query)
    ids, distances = manager.query(q_emb, top_k)

    # Handle empty results
    if not ids:
        return QueryResult(primary_result="", all_results=[])

    results = manager._collection.get(ids=ids)

    # Convert distances to cosine similarities (ChromaDB returns L2 distances)
    # Cosine similarity = 1 - (L2 distance^2 / 2)
    similarities = [1 - (d * d / 2) for d in distances]

    all_results = [
        EmbeddingResult(
            text=m.get("text", ""),
            similarity_score=sim,
            document_id=m.get("document_id", ""),
            document_name=m.get("document_name", ""),
            chunk_index=m.get("chunk_index", -1),
            record_id=id_,
            page_number=m.get("page_number", "unknown"),
        )
        for m, sim, id_ in zip(results["metadatas"], similarities, ids, strict=False)
    ]

    # Sort by similarity score in descending order
    all_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return QueryResult(
        primary_result=all_results[0]["text"] if all_results else "",
        all_results=all_results,
    )
