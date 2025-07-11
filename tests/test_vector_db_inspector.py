import pytest


def test_is_fts5_available():
    """Test the FTS5 availability check function."""
    from rag_pipeline.utils.vector_db_inspector import is_fts5_available

    # This should work on most systems, but may fail in CI environments
    result = is_fts5_available()
    assert isinstance(result, bool)


@pytest.mark.fts5
def test_inspect_chroma_schema(test_case_dir):
    pytest.importorskip("chromadb")

    from rag_pipeline.config.vector_store import VectorStoreConfig
    from rag_pipeline.core.vector_store import ChromaVectorStoreManager
    from rag_pipeline.utils.vector_db_inspector import inspect_chroma_schema, is_fts5_available

    # Skip test if FTS5 is not available (e.g., in CI environments)
    if not is_fts5_available():
        pytest.skip("SQLite FTS5 extension not available")

    config = VectorStoreConfig(host=None, persist_directory=test_case_dir)
    manager = ChromaVectorStoreManager(config)
    manager.add_embeddings(ids=["1"], embeddings=[[0.0, 0.1]], metadatas=[{"a": 1}])
    schema = inspect_chroma_schema(test_case_dir)
    assert "collections" in schema
    assert isinstance(schema["collections"], list)
