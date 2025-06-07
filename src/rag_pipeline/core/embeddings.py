"""Utility functions for processing PDFs and storing embeddings."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader

from rag_pipeline.config.vector_store import VectorStoreConfig
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


class QueryResult(TypedDict):
    """Result from querying embeddings."""

    primary_result: str
    all_results: list[EmbeddingResult]


__all__ = [
    "load_pdf_nodes",
    "embed_text_nodes",
    "store_embeddings",
    "process_pdf",
    "query_embeddings",
]


def load_pdf_nodes(
    pdf_path: str | Path,
    *,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    max_pages: int | None = None,
) -> list[Document]:
    """Load a PDF and split it into document nodes."""
    reader = PDFReader()
    docs = reader.load_data(Path(pdf_path))
    if max_pages is not None:
        docs = docs[:max_pages]

    parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return parser.get_nodes_from_documents(docs)


def embed_text_nodes(nodes: list[Document], model_name: str) -> list[list[float]]:
    """Embed text nodes using a HuggingFace model."""
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    return [embed_model.get_text_embedding(n.text) for n in nodes]


def generate_content_hash(text: str) -> str:
    """Generate a hash of the text content for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()


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
    """Process a PDF and store embeddings, returning counts."""
    pdf_path = Path(pdf_path)
    nodes = load_pdf_nodes(
        pdf_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_pages=max_pages,
    )

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
        )
        for m, sim, id_ in zip(results["metadatas"], similarities, ids, strict=False)
    ]

    # Sort by similarity score in descending order
    all_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return QueryResult(
        primary_result=all_results[0]["text"] if all_results else "",
        all_results=all_results,
    )
