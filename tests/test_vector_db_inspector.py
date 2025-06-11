import pytest


def test_inspect_chroma_schema(test_case_dir):
    pytest.importorskip("chromadb")
    from rag_pipeline.config.vector_store import VectorStoreConfig
    from rag_pipeline.core.vector_store import ChromaVectorStoreManager
    from rag_pipeline.utils.vector_db_inspector import inspect_chroma_schema

    config = VectorStoreConfig(host=None, persist_directory=test_case_dir)
    manager = ChromaVectorStoreManager(config)
    manager.add_embeddings(ids=["1"], embeddings=[[0.0, 0.1]], metadatas=[{"a": 1}])
    schema = inspect_chroma_schema(test_case_dir)
    assert "collections" in schema
    assert isinstance(schema["collections"], list)
