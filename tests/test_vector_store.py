"""Tests for vector store manager."""

from tempfile import TemporaryDirectory

from rag_pipeline.core.vector_store import ChromaVectorStoreManager
from rag_pipeline.config.vector_store import VectorStoreConfig


def test_chroma_manager_add_and_query() -> None:
    with TemporaryDirectory() as tmpdir:
        config = VectorStoreConfig(host=None, persist_directory=tmpdir)
        manager = ChromaVectorStoreManager(config)
        # simple 2d embeddings for test
        manager.add_embeddings(ids=["1"], embeddings=[[0.0, 0.1]], metadatas=[{}])
        result = manager.query([0.0, 0.1], top_k=1)
        assert result[0] == "1"
