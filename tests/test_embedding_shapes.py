import pytest

from rag_pipeline.config.parameter_sets import TEST_PARAMS


def test_embedding_shape():
    pytest.importorskip("llama_index")
    from llama_index.core import Document
    from rag_pipeline.core import embeddings

    docs = [Document(text="embedding shape test")]
    result = embeddings.embed_text_nodes(docs, TEST_PARAMS.embedding.model_name)
    assert len(result) == 1
    assert isinstance(result[0], list)
    assert all(isinstance(v, float) for v in result[0])
    assert len(result[0]) > 10
