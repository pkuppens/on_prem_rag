"""Tests for the setup_embedding_models.py script."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts import setup_embedding_models


class TestSetupEmbeddingModels:
    """Test the setup embedding models script."""

    def test_setup_cache_directories(self, tmp_path):
        """Test that cache directories are created correctly."""
        # Set up temporary cache directories
        hf_home = str(tmp_path / "huggingface")
        transformers_cache = str(tmp_path / "huggingface" / "hub")
        sentence_transformers_home = str(tmp_path / "huggingface" / "sentence_transformers")

        with patch.dict(
            os.environ,
            {
                "HF_HOME": hf_home,
                "TRANSFORMERS_CACHE": transformers_cache,
                "SENTENCE_TRANSFORMERS_HOME": sentence_transformers_home,
            },
        ):
            # Call the function
            result_hf_home, result_transformers_cache, result_sentence_transformers_home = (
                setup_embedding_models.setup_cache_directories()
            )

            # Verify directories were created
            assert Path(hf_home).exists()
            assert Path(transformers_cache).exists()
            assert Path(sentence_transformers_home).exists()

            # Verify return values
            assert result_hf_home == hf_home
            assert result_transformers_cache == transformers_cache
            assert result_sentence_transformers_home == sentence_transformers_home

    def test_setup_cache_directories_defaults(self, tmp_path, monkeypatch):
        """Test cache directory setup with default values."""
        # Mock the home directory
        mock_home = str(tmp_path)
        monkeypatch.setattr(os.path, "expanduser", lambda path: path.replace("~", mock_home))

        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            result_hf_home, result_transformers_cache, result_sentence_transformers_home = (
                setup_embedding_models.setup_cache_directories()
            )

            # Verify default paths
            expected_hf_home = f"{mock_home}/.cache/huggingface"
            expected_transformers_cache = f"{expected_hf_home}/hub"
            expected_sentence_transformers_home = f"{expected_hf_home}/sentence_transformers"

            assert result_hf_home == expected_hf_home
            assert result_transformers_cache == expected_transformers_cache
            assert result_sentence_transformers_home == expected_sentence_transformers_home

            # Verify directories were created
            assert Path(expected_hf_home).exists()
            assert Path(expected_transformers_cache).exists()
            assert Path(expected_sentence_transformers_home).exists()

    @patch("scripts.setup_embedding_models.SentenceTransformer")
    def test_download_sentence_transformer_model_success(self, mock_sentence_transformer):
        """Test successful sentence transformer model download."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.cache_folder = "/mock/cache/folder"
        mock_model.encode.return_value = [0.1, 0.2, 0.3]  # Mock embedding
        mock_sentence_transformer.return_value = mock_model

        # Test the function
        result = setup_embedding_models.download_sentence_transformer_model("test-model")

        # Verify
        assert result is True, "download_sentence_transformer_model should return True on successful download"
        mock_sentence_transformer.assert_called_once_with("test-model")
        mock_model.encode.assert_called_once_with("Test sentence")

    @patch("scripts.setup_embedding_models.SentenceTransformer")
    def test_download_sentence_transformer_model_failure(self, mock_sentence_transformer):
        """Test sentence transformer model download failure."""
        # Mock failure
        mock_sentence_transformer.side_effect = Exception("Download failed")

        # Test the function
        result = setup_embedding_models.download_sentence_transformer_model("test-model")

        # Verify
        assert result is False, "download_sentence_transformer_model should return False when download fails"
        mock_sentence_transformer.assert_called_once_with("test-model")

    @patch("scripts.setup_embedding_models.AutoModel")
    @patch("scripts.setup_embedding_models.AutoTokenizer")
    def test_download_transformers_model_success(self, mock_tokenizer, mock_model):
        """Test successful transformers model download."""
        # Mock the tokenizer and model
        mock_tokenizer_instance = MagicMock()
        mock_model_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance

        # Mock tokenizer return
        mock_tokenizer_instance.return_value = {"input_ids": "mock_input"}

        # Mock model output
        mock_output = MagicMock()
        mock_output.last_hidden_state.shape = (1, 10, 384)  # Mock shape
        mock_model_instance.return_value = mock_output

        # Test the function
        result = setup_embedding_models.download_transformers_model("test-model")

        # Verify
        assert result is True, "download_transformers_model should return True on successful download"
        mock_tokenizer.from_pretrained.assert_called_once_with("test-model")
        mock_model.from_pretrained.assert_called_once_with("test-model")

    @patch("scripts.setup_embedding_models.AutoModel")
    @patch("scripts.setup_embedding_models.AutoTokenizer")
    def test_download_transformers_model_failure(self, mock_tokenizer, mock_model):
        """Test transformers model download failure."""
        # Mock failure
        mock_tokenizer.from_pretrained.side_effect = Exception("Download failed")

        # Test the function
        result = setup_embedding_models.download_transformers_model("test-model")

        # Verify
        assert result is False, "download_transformers_model should return False when download fails"
        mock_tokenizer.from_pretrained.assert_called_once_with("test-model")

    @patch("scripts.setup_embedding_models.HuggingFaceEmbedding")
    def test_download_llamaindex_embedding_success(self, mock_hf_embedding):
        """Test successful LlamaIndex embedding model download."""
        # Mock the embedding model
        mock_embedding_instance = MagicMock()
        mock_embedding_instance.get_text_embedding.return_value = [0.1, 0.2, 0.3]
        mock_hf_embedding.return_value = mock_embedding_instance

        # Test the function
        result = setup_embedding_models.download_llamaindex_embedding("test-model")

        # Verify
        assert result is True, "download_llamaindex_embedding should return True on successful download"
        mock_hf_embedding.assert_called_once_with(model_name="test-model")
        mock_embedding_instance.get_text_embedding.assert_called_once_with("Test sentence")

    @patch("scripts.setup_embedding_models.HuggingFaceEmbedding")
    def test_download_llamaindex_embedding_failure(self, mock_hf_embedding):
        """Test LlamaIndex embedding model download failure."""
        # Mock failure
        mock_hf_embedding.side_effect = Exception("Download failed")

        # Test the function
        result = setup_embedding_models.download_llamaindex_embedding("test-model")

        # Verify
        assert result is False, "download_llamaindex_embedding should return False when download fails"
        mock_hf_embedding.assert_called_once_with(model_name="test-model")

    def test_script_imports(self):
        """Test that the script can be imported without errors."""
        # This test verifies the script has correct imports and syntax
        assert hasattr(setup_embedding_models, "main")
        assert hasattr(setup_embedding_models, "setup_cache_directories")
        assert hasattr(setup_embedding_models, "download_sentence_transformer_model")
        assert hasattr(setup_embedding_models, "download_transformers_model")
        assert hasattr(setup_embedding_models, "download_llamaindex_embedding")

    @pytest.mark.slow
    def test_script_execution_dry_run(self, tmp_path, monkeypatch):
        """Test script execution without actually downloading models."""
        # Set up temporary cache directories using environment variables
        # This is more reliable than mocking expanduser
        hf_home = str(tmp_path / "huggingface")
        transformers_cache = str(tmp_path / "huggingface" / "hub")
        sentence_transformers_home = str(tmp_path / "huggingface" / "sentence_transformers")

        # Set environment variables to override defaults
        with patch.dict(
            os.environ,
            {
                "HF_HOME": hf_home,
                "TRANSFORMERS_CACHE": transformers_cache,
                "SENTENCE_TRANSFORMERS_HOME": sentence_transformers_home,
            },
        ):
            # Mock all download functions to return True without actual downloads
            with (
                patch("scripts.setup_embedding_models.download_sentence_transformer_model", return_value=True),
                patch("scripts.setup_embedding_models.download_transformers_model", return_value=True),
                patch("scripts.setup_embedding_models.download_llamaindex_embedding", return_value=True),
            ):
                # Test the main function
                result = setup_embedding_models.main()

                # Verify main function succeeded
                assert result is True, "main() function should return True when all downloads succeed"

                # Verify cache directories were created using Path objects for cross-platform compatibility
                assert Path(hf_home).exists(), f"HF_HOME directory should exist at: {hf_home}"
                assert Path(transformers_cache).exists(), f"TRANSFORMERS_CACHE directory should exist at: {transformers_cache}"
                assert Path(sentence_transformers_home).exists(), (
                    f"SENTENCE_TRANSFORMERS_HOME directory should exist at: {sentence_transformers_home}"
                )
