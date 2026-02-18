"""LLM backend configuration from environment variables.

This module provides LLM_BACKEND and LLM_MODEL resolution for the RAG pipeline.
Switching backend is done by changing an env var. See docs/technical/LLM.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Supported backends; LiteLLM model prefix for each
BACKEND_TO_PREFIX: dict[str, str] = {
    "ollama": "ollama",
    "openai": "openai",
    "anthropic": "anthropic",
    "azure": "azure",
    "huggingface": "huggingface",
}

DEFAULT_BACKEND = "ollama"
DEFAULT_MODEL = "mistral"


def _normalize_backend(value: str) -> str:
    """Normalize backend name to lowercase."""
    return value.strip().lower()


@dataclass
class LLMConfig:
    """Resolved LLM configuration from environment."""

    backend: str
    model: str
    litellm_model: str
    api_base: str | None

    @property
    def backend_model_pair(self) -> str:
        """Human-readable backend/model for logging."""
        return f"{self.backend}/{self.model}"


def get_llm_config() -> LLMConfig:
    """Resolve LLM configuration from LLM_BACKEND and LLM_MODEL env vars.

    Returns:
        LLMConfig with backend, model, LiteLLM model string, and optional api_base.

    Example:
        LLM_BACKEND=ollama LLM_MODEL=mistral -> litellm_model='ollama/mistral'
        LLM_BACKEND=openai LLM_MODEL=gpt-4 -> litellm_model='openai/gpt-4'
    """
    backend = _normalize_backend(os.getenv("LLM_BACKEND", DEFAULT_BACKEND))
    model = (os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL") or DEFAULT_MODEL).strip()

    if backend not in BACKEND_TO_PREFIX:
        raise ValueError(f"Unknown LLM_BACKEND '{backend}'. Supported: {', '.join(BACKEND_TO_PREFIX)}")

    prefix = BACKEND_TO_PREFIX[backend]
    # Azure uses deployment name; model may already include "azure/"
    if backend == "azure":
        litellm_model = model if model.startswith("azure/") else f"azure/{model}"
    else:
        litellm_model = f"{prefix}/{model}"

    api_base: str | None = None
    if backend == "ollama":
        api_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    return LLMConfig(
        backend=backend,
        model=model,
        litellm_model=litellm_model,
        api_base=api_base,
    )
