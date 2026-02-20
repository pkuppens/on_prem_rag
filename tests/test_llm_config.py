"""Tests for LLM configuration.

As a user I want LLM_BACKEND and LLM_MODEL to control which provider is used,
so I can switch backends by changing env vars.
Technical: get_llm_config() resolves LITTELLM model string from env.
"""

import os
from unittest.mock import patch

import pytest

from backend.rag_pipeline.config.llm_config import (
    DEFAULT_BACKEND,
    DEFAULT_MODEL,
    LLMConfig,
    get_litellm_model_for_backend,
    get_llm_config,
    get_model_for_backend,
)


class TestLLMConfig:
    """Test LLM config resolution from environment."""

    def test_default_config(self):
        """Default backend is ollama, model mistral, with ollama prefix."""
        with patch.dict(os.environ, {}, clear=False):
            for key in ("LLM_BACKEND", "LLM_MODEL", "OLLAMA_MODEL", "OLLAMA_BASE_URL"):
                os.environ.pop(key, None)
            config = get_llm_config()
        assert config.backend == DEFAULT_BACKEND
        assert config.model == DEFAULT_MODEL
        assert config.litellm_model == f"ollama/{DEFAULT_MODEL}"
        assert config.api_base == "http://localhost:11434"

    def test_ollama_with_ollama_model_env(self):
        """OLLAMA_MODEL is used when LLM_MODEL not set (backward compat)."""
        with patch.dict(os.environ, {"OLLAMA_MODEL": "llama3.2:1b"}, clear=False):
            os.environ.pop("LLM_BACKEND", None)
            os.environ.pop("LLM_MODEL", None)
            config = get_llm_config()
        assert config.backend == "ollama"
        assert config.model == "llama3.2:1b"
        assert config.litellm_model == "ollama/llama3.2:1b"
        assert config.api_base is not None

    def test_llm_backend_openai(self):
        """LLM_BACKEND=openai produces openai/gpt-4 model string."""
        with patch.dict(os.environ, {"LLM_BACKEND": "openai", "LLM_MODEL": "gpt-4"}, clear=False):
            config = get_llm_config()
        assert config.backend == "openai"
        assert config.model == "gpt-4"
        assert config.litellm_model == "openai/gpt-4"
        assert config.api_base is None

    def test_llm_backend_anthropic(self):
        """LLM_BACKEND=anthropic produces anthropic/ model string."""
        with patch.dict(
            os.environ,
            {"LLM_BACKEND": "anthropic", "LLM_MODEL": "claude-2"},
            clear=False,
        ):
            config = get_llm_config()
        assert config.litellm_model == "anthropic/claude-2"

    def test_llm_backend_azure(self):
        """LLM_BACKEND=azure uses deployment name in model string."""
        with patch.dict(os.environ, {"LLM_BACKEND": "azure", "LLM_MODEL": "my-deployment"}, clear=False):
            config = get_llm_config()
        assert config.litellm_model == "azure/my-deployment"

    def test_llm_backend_gemini(self):
        """LLM_BACKEND=gemini produces gemini/ model string."""
        with patch.dict(
            os.environ,
            {"LLM_BACKEND": "gemini", "LLM_MODEL": "gemini-2.0-flash"},
            clear=False,
        ):
            config = get_llm_config()
        assert config.backend == "gemini"
        assert config.model == "gemini-2.0-flash"
        assert config.litellm_model == "gemini/gemini-2.0-flash"
        assert config.api_base is None

    def test_llm_backend_gemini_uses_llm_model_gemini_when_llm_model_unset(self):
        """LLM_MODEL_GEMINI used when LLM_MODEL not set and backend is gemini."""
        with patch.dict(
            os.environ,
            {"LLM_BACKEND": "gemini", "LLM_MODEL_GEMINI": "gemini-1.5-pro"},
            clear=False,
        ):
            os.environ.pop("LLM_MODEL", None)
            config = get_llm_config()
        assert config.litellm_model == "gemini/gemini-1.5-pro"

    def test_unknown_backend_raises(self):
        """Unknown LLM_BACKEND raises ValueError."""
        with patch.dict(os.environ, {"LLM_BACKEND": "unknown", "LLM_MODEL": "x"}, clear=False):
            with pytest.raises(ValueError, match="Unknown LLM_BACKEND"):
                get_llm_config()

    def test_get_litellm_model_for_backend_uses_env(self):
        """get_litellm_model_for_backend uses LLM_MODEL_GEMINI when set."""
        with patch.dict(
            os.environ,
            {"LLM_MODEL_GEMINI": "gemini-1.5-pro"},
            clear=False,
        ):
            result = get_litellm_model_for_backend("gemini")
        assert result == "gemini/gemini-1.5-pro"

    def test_get_model_for_backend_returns_model_name_only(self):
        """get_model_for_backend returns model name without prefix."""
        with patch.dict(os.environ, {}, clear=False):
            for key in ("LLM_MODEL", "LLM_MODEL_GEMINI", "OLLAMA_MODEL"):
                os.environ.pop(key, None)
        result = get_model_for_backend("gemini")
        assert result == "gemini-2.0-flash"
        assert "/" not in result

    def test_backend_model_pair(self):
        """backend_model_pair returns human-readable string for logging."""
        config = LLMConfig(backend="ollama", model="mistral", litellm_model="ollama/mistral", api_base="x")
        assert config.backend_model_pair == "ollama/mistral"
