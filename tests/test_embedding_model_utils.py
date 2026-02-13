"""Tests for embedding model retrieval utilities."""

from pathlib import Path
from unittest.mock import patch

from backend.rag_pipeline.utils.embedding_model_utils import get_embedding_model


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
