"""Tests for vector store manager."""

import pytest

pytest.importorskip("chromadb")

from rag_pipeline.config.vector_store import VectorStoreConfig
from rag_pipeline.core.vector_store import ChromaVectorStoreManager


# @pytest.mark.xfail(
#     sys.platform.startswith("win"),
#     reason=(
#         "ChromaDB/SQLite keeps files open on Windows, causing PermissionError "
#         "when cleaning up TemporaryDirectory. "
#         "Recommended: Use a gitignored test data directory for persistence "
#         "and clean up manually in setup/teardown."
#     )
# )
class TestChromaVectorStoreManager:
    """Test ChromaDB vector store manager."""

    def test_add_and_query(self, test_case_dir):
        """Test adding and querying embeddings."""
        config = VectorStoreConfig(host=None, persist_directory=str(test_case_dir))
        manager = ChromaVectorStoreManager(config)

        # Simple 2d embeddings for test
        manager.add_embeddings(ids=["1"], embeddings=[[0.0, 0.1]], metadatas=[{"test": "value"}])
        result = manager.query([0.0, 0.1], top_k=1)

        # Query returns (ids, distances) tuple
        ids, distances = result
        print(f"Query returned: ids={ids}, distances={distances}")
        assert isinstance(ids, list), f"Expected ids to be list, got {type(ids)}"
        assert len(ids) == 1, f"Expected 1 id, got {len(ids)}"
        assert ids[0] == "1", f"Expected first id to be '1', got '{ids[0]}'"

        # Cleanup to release file locks on Windows
        del manager
        import gc

        gc.collect()

    def test_get_chunk_count_and_get_all_chunks(self, test_case_dir):
        """As a user I want metrics and BM25 to use the abstract interface.
        Technical: get_chunk_count and get_all_chunks work via ABC.
        """
        config = VectorStoreConfig(host=None, persist_directory=str(test_case_dir), collection_name="test_chunks_abc")
        manager = ChromaVectorStoreManager(config)

        manager.add_embeddings(
            ids=["c1", "c2"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            metadatas=[{"text": "hello world", "chunk_index": 0}, {"text": "foo bar", "chunk_index": 1}],
        )

        assert manager.get_chunk_count() == 2

        ids, texts, metadatas = manager.get_all_chunks(limit=100)
        assert ids == ["c1", "c2"]
        assert texts == ["hello world", "foo bar"]
        assert len(metadatas) == 2
        assert metadatas[0].get("chunk_index") == 0

        del manager
        import gc

        gc.collect()
