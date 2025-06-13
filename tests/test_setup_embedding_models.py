"""Tests for the setup_embedding_models.py script."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("llama_index", reason="missing deps")
from backend.rag_pipeline.utils.directory_utils import get_cache_dir, get_project_root
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
        """Test cache directory setup with default values.

        This test verifies that:
        1. When no environment variables are set, the cache directories are created in the project's data/cache directory
        2. The subdirectories (hub and sentence_transformers) are created correctly
        3. The paths returned match the expected project structure
        """
        # Mock the project root to use tmp_path
        mock_project_root = tmp_path
        monkeypatch.setattr("backend.rag_pipeline.utils.directory_utils.get_project_root", lambda: mock_project_root)

        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            # Call the function
            result_hf_home, result_transformers_cache, result_sentence_transformers_home = (
                setup_embedding_models.setup_cache_directories()
            )

            # Calculate expected paths
            expected_hf_home = str(mock_project_root / "data" / "cache" / "huggingface")
            expected_transformers_cache = f"{expected_hf_home}/hub"
            expected_sentence_transformers_home = f"{expected_hf_home}/sentence_transformers"

            # Debug information
            print("\nDebug Information:")
            print(f"Mock project root: {mock_project_root}")
            print(f"Expected HF_HOME: {expected_hf_home}")
            print(f"Actual HF_HOME: {result_hf_home}")
            print(f"Expected TRANSFORMERS_CACHE: {expected_transformers_cache}")
            print(f"Actual TRANSFORMERS_CACHE: {result_transformers_cache}")
            print(f"Expected SENTENCE_TRANSFORMERS_HOME: {expected_sentence_transformers_home}")
            print(f"Actual SENTENCE_TRANSFORMERS_HOME: {result_sentence_transformers_home}")

            # Verify paths match
            assert result_hf_home == expected_hf_home, (
                f"HF_HOME path mismatch:\nExpected: {expected_hf_home}\nGot: {result_hf_home}"
            )
            assert result_transformers_cache == expected_transformers_cache, (
                f"TRANSFORMERS_CACHE path mismatch:\nExpected: {expected_transformers_cache}\nGot: {result_transformers_cache}"
            )
            assert result_sentence_transformers_home == expected_sentence_transformers_home, (
                f"SENTENCE_TRANSFORMERS_HOME path mismatch:\n"
                f"Expected: {expected_sentence_transformers_home}\n"
                f"Got: {result_sentence_transformers_home}"
            )

            # Verify directories were created
            assert Path(expected_hf_home).exists(), f"HF_HOME directory not created at: {expected_hf_home}"
            assert Path(expected_transformers_cache).exists(), (
                f"TRANSFORMERS_CACHE directory not created at: {expected_transformers_cache}"
            )
            assert Path(expected_sentence_transformers_home).exists(), (
                f"SENTENCE_TRANSFORMERS_HOME directory not created at: {expected_sentence_transformers_home}"
            )

            # Verify directory structure
            hf_home_path = Path(expected_hf_home)
            assert hf_home_path.is_dir(), f"HF_HOME is not a directory: {expected_hf_home}"
            assert Path(expected_transformers_cache).is_dir(), (
                f"TRANSFORMERS_CACHE is not a directory: {expected_transformers_cache}"
            )
            assert Path(expected_sentence_transformers_home).is_dir(), (
                f"SENTENCE_TRANSFORMERS_HOME is not a directory: {expected_sentence_transformers_home}"
            )

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

    @patch("scripts.setup_embedding_models.SentenceTransformer")
    def test_download_sentence_transformer_model_failure(self, mock_sentence_transformer):
        """Test sentence transformer model download failure."""
        # Mock failure
        mock_sentence_transformer.side_effect = Exception("Download failed")

        # Test the function
        result = setup_embedding_models.download_sentence_transformer_model("test-model")

        # Verify
        assert result is False, "download_sentence_transformer_model should return False when download fails"

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

    @patch("scripts.setup_embedding_models.HuggingFaceEmbedding")
    def test_download_llamaindex_embedding_failure(self, mock_hf_embedding):
        """Test LlamaIndex embedding model download failure."""
        # Mock failure
        mock_hf_embedding.side_effect = Exception("Download failed")

        # Test the function
        result = setup_embedding_models.download_llamaindex_embedding("test-model")

        # Verify
        assert result is False, "download_llamaindex_embedding should return False when download fails"

    def test_script_imports(self):
        """Test that all imports work correctly."""
        # Test importing the script works
        import scripts.setup_embedding_models

        # Test that required functions exist
        assert hasattr(scripts.setup_embedding_models, "setup_cache_directories")
        assert hasattr(scripts.setup_embedding_models, "download_sentence_transformer_model")
        assert hasattr(scripts.setup_embedding_models, "download_transformers_model")
        assert hasattr(scripts.setup_embedding_models, "download_llamaindex_embedding")

    @pytest.mark.slow
    def test_script_execution_dry_run(self, tmp_path, monkeypatch):
        """Test script execution in dry run mode."""
        # Mock the project root to use tmp_path
        mock_project_root = tmp_path
        monkeypatch.setattr("backend.rag_pipeline.utils.directory_utils.get_project_root", lambda: mock_project_root)

        # Mock sys.argv to include dry-run
        test_argv = ["setup_embedding_models.py", "--dry-run"]
        monkeypatch.setattr("sys.argv", test_argv)

        # Mock all download functions to avoid actual downloads
        with (
            patch("scripts.setup_embedding_models.download_sentence_transformer_model") as mock_st,
            patch("scripts.setup_embedding_models.download_transformers_model") as mock_tr,
            patch("scripts.setup_embedding_models.download_llamaindex_embedding") as mock_li,
        ):
            # Set up mocks to return success
            mock_st.return_value = True
            mock_tr.return_value = True
            mock_li.return_value = True

            # Import and run main
            from scripts.setup_embedding_models import main

            # This should execute without errors
            main()

            # Verify that download functions were not called in dry-run mode
            mock_st.assert_not_called()
            mock_tr.assert_not_called()
            mock_li.assert_not_called()

    @pytest.mark.slow
    @pytest.mark.requires_internet
    def test_real_model_download_sentence_transformer(self, tmp_path, monkeypatch):
        """Download a small model from Hugging Face and verify caching.

        This integration test checks that ``download_sentence_transformer_model``
        can retrieve an actual model when internet access is available. The
        expected behaviour is:
        1. The function returns ``True`` to indicate success.
        2. The cache directory contains at least one file after download.
        The test is skipped automatically when internet connectivity is missing.
        """
        # Use a very small model for testing
        test_model = "sentence-transformers/all-MiniLM-L6-v2"

        # Mock the project root to use tmp_path
        mock_project_root = tmp_path
        monkeypatch.setattr("backend.rag_pipeline.utils.directory_utils.get_project_root", lambda: mock_project_root)

        # Set up cache directories in tmp_path
        cache_dir = tmp_path / "cache" / "huggingface"
        monkeypatch.setenv("HF_HOME", str(cache_dir))
        monkeypatch.setenv("SENTENCE_TRANSFORMERS_HOME", str(cache_dir / "sentence_transformers"))

        # Setup cache directories
        setup_embedding_models.setup_cache_directories()

        # Check if we're in offline mode
        if os.environ.get("TRANSFORMERS_OFFLINE") == "1":
            pytest.skip("Test requires internet access but TRANSFORMERS_OFFLINE=1")

        try:
            # Download the model
            result = setup_embedding_models.download_sentence_transformer_model(test_model)

            # Verify successful download
            assert result is True, (
                f"Failed to download model: {test_model}. "
                "This could be due to:\n"
                "1. No internet connection\n"
                "2. Hugging Face servers are down\n"
                "3. Model name is incorrect\n"
                "4. Cache directory permissions issues"
            )

            # Verify cache directory contains model files
            cache_path = Path(cache_dir / "sentence_transformers")
            assert cache_path.exists(), f"Cache directory should exist after model download. Expected path: {cache_path}"

            # The model should be cached somewhere in the directory structure
            cached_files = list(cache_path.rglob("*"))
            assert len(cached_files) > 0, (
                "No files were cached. This could be due to:\n"
                "1. Network access issues\n"
                "2. Incorrect model name\n"
                "3. Cache directory permissions\n"
                f"Cache path: {cache_path}"
            )

        except Exception as e:
            pytest.fail(
                f"Test failed with error: {str(e)}\n"
                "This could be due to:\n"
                "1. Network connectivity issues\n"
                "2. Hugging Face API changes\n"
                "3. Model repository access issues"
            )

    @patch("scripts.setup_embedding_models.SentenceTransformer")
    def test_download_sentence_transformer_model_offline_success(self, mock_sentence_transformer):
        """Test successful sentence transformer model download in offline mode."""
        # Set offline mode
        with patch.dict(os.environ, {"TRANSFORMERS_OFFLINE": "1"}):
            # Mock the model
            mock_model = MagicMock()
            mock_model.cache_folder = "/mock/cache/folder"
            mock_model.encode.return_value = [0.1, 0.2, 0.3]  # Mock embedding
            mock_sentence_transformer.return_value = mock_model

            # Test the function
            result = setup_embedding_models.download_sentence_transformer_model("test-model")

            # Verify
            assert result is True, "download_sentence_transformer_model should return True on successful offline load"
            # Only verify the model name is passed, ignore other parameters
            mock_sentence_transformer.assert_called_once()
            assert mock_sentence_transformer.call_args[0][0] == "test-model"
            mock_model.encode.assert_called_once_with("Test sentence")

    @patch("scripts.setup_embedding_models.AutoModel")
    @patch("scripts.setup_embedding_models.AutoTokenizer")
    def test_download_transformers_model_offline_success(self, mock_tokenizer, mock_model):
        """Test successful transformers model download in offline mode."""
        # Set offline mode
        with patch.dict(os.environ, {"TRANSFORMERS_OFFLINE": "1"}):
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
            assert result is True, "download_transformers_model should return True on successful offline load"
            # Only verify the model name and local_files_only are passed, ignore other parameters
            mock_tokenizer.from_pretrained.assert_called_once()
            assert mock_tokenizer.from_pretrained.call_args[0][0] == "test-model"
            assert mock_tokenizer.from_pretrained.call_args[1].get("local_files_only") is True
            
            mock_model.from_pretrained.assert_called_once()
            assert mock_model.from_pretrained.call_args[0][0] == "test-model"
            assert mock_model.from_pretrained.call_args[1].get("local_files_only") is True

    @patch("scripts.setup_embedding_models.HuggingFaceEmbedding")
    def test_download_llamaindex_embedding_offline_success(self, mock_hf_embedding):
        """Test successful LlamaIndex embedding model download in offline mode."""
        # Set offline mode
        with patch.dict(os.environ, {"TRANSFORMERS_OFFLINE": "1"}):
            # Mock the embedding model
            mock_embedding_instance = MagicMock()
            mock_embedding_instance.get_text_embedding.return_value = [0.1, 0.2, 0.3]
            mock_hf_embedding.return_value = mock_embedding_instance

            # Test the function
            result = setup_embedding_models.download_llamaindex_embedding("test-model")

            # Verify
            assert result is True, "download_llamaindex_embedding should return True on successful offline load"
            # Only verify the model name and local_files_only are passed, ignore other parameters
            mock_hf_embedding.assert_called_once()
            assert mock_hf_embedding.call_args[1].get("model_name") == "test-model"
            assert mock_hf_embedding.call_args[1].get("local_files_only") is True
            mock_embedding_instance.get_text_embedding.assert_called_once_with("Test sentence")

    @patch("scripts.setup_embedding_models.SentenceTransformer")
    def test_download_sentence_transformer_model_offline_failure(self, mock_sentence_transformer):
        """Test sentence transformer model download failure in offline mode."""
        # Set offline mode
        with patch.dict(os.environ, {"TRANSFORMERS_OFFLINE": "1"}):
            # Mock failure
            mock_sentence_transformer.side_effect = Exception("Model not found in cache")

            # Test the function
            result = setup_embedding_models.download_sentence_transformer_model("test-model")

            # Verify
            assert result is False, "download_sentence_transformer_model should return False when offline load fails"
            # Only verify the model name is passed, ignore other parameters
            mock_sentence_transformer.assert_called_once()
            assert mock_sentence_transformer.call_args[0][0] == "test-model"

    @patch("scripts.setup_embedding_models.AutoModel")
    @patch("scripts.setup_embedding_models.AutoTokenizer")
    def test_download_transformers_model_offline_failure(self, mock_tokenizer, mock_model):
        """Test transformers model download failure in offline mode."""
        # Set offline mode
        with patch.dict(os.environ, {"TRANSFORMERS_OFFLINE": "1"}):
            # Mock failure
            mock_tokenizer.from_pretrained.side_effect = Exception("Model not found in cache")

            # Test the function
            result = setup_embedding_models.download_transformers_model("test-model")

            # Verify
            assert result is False, "download_transformers_model should return False when offline load fails"
            # Only verify the model name and local_files_only are passed, ignore other parameters
            mock_tokenizer.from_pretrained.assert_called_once()
            assert mock_tokenizer.from_pretrained.call_args[0][0] == "test-model"
            assert mock_tokenizer.from_pretrained.call_args[1].get("local_files_only") is True

    @patch("scripts.setup_embedding_models.HuggingFaceEmbedding")
    def test_download_llamaindex_embedding_offline_failure(self, mock_hf_embedding):
        """Test LlamaIndex embedding model download failure in offline mode."""
        # Set offline mode
        with patch.dict(os.environ, {"TRANSFORMERS_OFFLINE": "1"}):
            # Mock failure
            mock_hf_embedding.side_effect = Exception("Model not found in cache")

            # Test the function
            result = setup_embedding_models.download_llamaindex_embedding("test-model")

            # Verify
            assert result is False, "download_llamaindex_embedding should return False when offline load fails"
            # Only verify the model name and local_files_only are passed, ignore other parameters
            mock_hf_embedding.assert_called_once()
            assert mock_hf_embedding.call_args[1].get("model_name") == "test-model"
            assert mock_hf_embedding.call_args[1].get("local_files_only") is True
