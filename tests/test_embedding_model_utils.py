"""Tests for embedding model retrieval utilities."""

from pathlib import Path
from unittest.mock import patch

from backend.rag_pipeline.utils.embedding_model_utils import (
    clear_embedding_model_cache,
    get_embedding_model,
)


@patch("backend.rag_pipeline.utils.embedding_model_utils.HuggingFaceEmbedding")
def test_get_embedding_model_local_path(mock_hf):
    """Load model from local path when path exists."""
    tmp_path = Path("/tmp/local-model")
    tmp_path.mkdir(parents=True, exist_ok=True)
    model = get_embedding_model(str(tmp_path))
    mock_hf.assert_called_once_with(model_name=str(tmp_path), local_files_only=True)
    assert model == mock_hf.return_value


@patch("backend.rag_pipeline.utils.embedding_model_utils.HuggingFaceEmbedding")
def test_get_embedding_model_remote(mock_hf, monkeypatch):
    """Load model from hub with cache dir and offline flag."""
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    model = get_embedding_model("remote-model", cache_dir="cache")
    mock_hf.assert_called_once_with(model_name="remote-model", cache_folder="cache", local_files_only=True)
    assert model == mock_hf.return_value


@patch("backend.rag_pipeline.utils.embedding_model_utils.HuggingFaceEmbedding")
def test_get_embedding_model_returns_cached_instance(mock_hf, monkeypatch):
    """As a user I want the embedding model cached, so that ingestion avoids cold-start per document.
    Technical: Second call with same (model_name, cache_dir) returns cached instance; HuggingFaceEmbedding
    is only called once.
    """
    monkeypatch.delenv("TRANSFORMERS_OFFLINE", raising=False)
    clear_embedding_model_cache()
    model1 = get_embedding_model("cached-model", cache_dir="cache")
    model2 = get_embedding_model("cached-model", cache_dir="cache")
    assert model1 is model2
    mock_hf.assert_called_once_with(model_name="cached-model", cache_folder="cache", local_files_only=False)


@patch("backend.rag_pipeline.utils.embedding_model_utils.HuggingFaceEmbedding")
def test_clear_embedding_model_cache_forces_reload(mock_hf):
    """As a user I want to clear the cache when switching models, so I can free memory or load a different model.
    Technical: After clear_embedding_model_cache(), next get_embedding_model call loads again.
    """
    clear_embedding_model_cache()
    get_embedding_model("reload-model")
    clear_embedding_model_cache()
    get_embedding_model("reload-model")
    assert mock_hf.call_count == 2
