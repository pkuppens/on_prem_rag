"""Utility functions for processing PDFs and storing embeddings."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader

from rag_pipeline.config.vector_store import VectorStoreConfig
from rag_pipeline.core.vector_store import ChromaVectorStoreManager

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


def embed_text_nodes(nodes: Sequence[Document], model_name: str) -> list[list[float]]:
    """Return embeddings for each node text."""
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    return [embed_model.get_text_embedding(node.text) for node in nodes]


def store_embeddings(
    ids: Iterable[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict] | None,
    persist_dir: str,
    collection_name: str = "documents",
) -> ChromaVectorStoreManager:
    """Store embeddings in a Chroma vector store."""
    config = VectorStoreConfig(host=None, persist_directory=persist_dir, collection_name=collection_name)
    manager = ChromaVectorStoreManager(config)
    manager.add_embeddings(
        ids=list(ids), embeddings=[list(e) for e in embeddings], metadatas=list(metadatas) if metadatas else None
    )
    return manager


def process_pdf(
    pdf_path: str | Path,
    model_name: str,
    *,
    persist_dir: str,
    collection_name: str = "documents",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    max_pages: int | None = None,
) -> tuple[int, int]:
    """Process a PDF and store embeddings, returning counts."""
    nodes = load_pdf_nodes(
        pdf_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_pages=max_pages,
    )
    embeddings = embed_text_nodes(nodes, model_name)
    metadatas = [{"text": n.text} for n in nodes]
    manager = store_embeddings(
        [n.node_id for n in nodes],
        embeddings,
        metadatas,
        persist_dir,
        collection_name,
    )
    count = manager._collection.count()
    return len(nodes), count


def query_embeddings(
    query: str,
    model_name: str,
    *,
    persist_dir: str,
    collection_name: str = "documents",
    top_k: int = 3,
) -> list[str]:
    """Query the persisted embeddings and return texts."""
    config = VectorStoreConfig(host=None, persist_directory=persist_dir, collection_name=collection_name)
    manager = ChromaVectorStoreManager(config)
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    q_emb = embed_model.get_query_embedding(query)
    ids = manager.query(q_emb, top_k)
    results = manager._collection.get(ids=ids)
    return [m.get("text", "") for m in results["metadatas"]]
