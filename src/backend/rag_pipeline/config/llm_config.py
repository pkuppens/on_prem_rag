"""LLM backend configuration from environment variables.

This module provides LLM_BACKEND and LLM_MODEL resolution for the RAG pipeline.
Switching backend is done by changing an env var. See docs/technical/LLM.md.

Model names are read from env vars to avoid hardcoding; providers deprecate
models over time. Use LLM_MODEL for global override, or LLM_MODEL_{BACKEND}
for backend-specific defaults (e.g. LLM_MODEL_GEMINI, LLM_MODEL_OPENAI).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from backend.shared.utils.env_utils import get_env, get_env_or_none

# Supported backends; LiteLLM model prefix for each
BACKEND_TO_PREFIX: dict[str, str] = {
    "ollama": "ollama",
    "openai": "openai",
    "anthropic": "anthropic",
    "azure": "azure",
    "huggingface": "huggingface",
    "gemini": "gemini",
}

DEFAULT_BACKEND = "ollama"

# Fallback model names per backend when no env var is set.
# Override via LLM_MODEL (global) or LLM_MODEL_{BACKEND} (e.g. LLM_MODEL_GEMINI).
BACKEND_DEFAULT_MODELS: dict[str, str] = {
    "ollama": "mistral",
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-sonnet-4-6",
    "azure": "gpt-4.1-mini",
    "huggingface": "mistralai/Mistral-7B-Instruct-v0.2",
    "gemini": "gemini-2.0-flash",
}

# Env var for backend-specific model override (used when LLM_MODEL not set)
BACKEND_MODEL_ENV_VARS: dict[str, str] = {
    "ollama": "OLLAMA_MODEL",  # Legacy name; also checked when backend=ollama
    "openai": "LLM_MODEL_OPENAI",
    "anthropic": "LLM_MODEL_ANTHROPIC",
    "azure": "LLM_MODEL_AZURE",
    "huggingface": "LLM_MODEL_HUGGINGFACE",
    "gemini": "LLM_MODEL_GEMINI",
}

DEFAULT_MODEL = BACKEND_DEFAULT_MODELS["ollama"]  # Backward compat for tests


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


def _resolve_model(backend: str) -> str:
    """Resolve model name for backend: LLM_MODEL > OLLAMA_MODEL > LLM_MODEL_{BACKEND} > default."""
    model = get_env_or_none("LLM_MODEL")
    if model:
        return model
    if backend == "ollama":
        model = get_env_or_none("OLLAMA_MODEL")
        if model:
            return model
    env_var = BACKEND_MODEL_ENV_VARS.get(backend)
    if env_var:
        model = get_env_or_none(env_var)
        if model:
            return model
    return BACKEND_DEFAULT_MODELS.get(backend, "mistral")


def get_llm_config() -> LLMConfig:
    """Resolve LLM configuration from LLM_BACKEND and LLM_MODEL env vars.

    Model resolution order: LLM_MODEL > OLLAMA_MODEL (ollama) > LLM_MODEL_{BACKEND} > default.

    Returns:
        LLMConfig with backend, model, LiteLLM model string, and optional api_base.

    Example:
        LLM_BACKEND=ollama LLM_MODEL=mistral -> litellm_model='ollama/mistral'
        LLM_BACKEND=gemini LLM_MODEL_GEMINI=gemini-2.0-flash -> litellm_model='gemini/gemini-2.0-flash'
    """
    backend = _normalize_backend(get_env("LLM_BACKEND", DEFAULT_BACKEND))
    model = _resolve_model(backend)

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
        api_base = get_env("OLLAMA_BASE_URL", "http://localhost:11434")

    return LLMConfig(
        backend=backend,
        model=model,
        litellm_model=litellm_model,
        api_base=api_base,
    )


def get_model_for_backend(backend: str) -> str:
    """Get model name (without LiteLLM prefix) for backend. Uses env resolution."""
    backend = _normalize_backend(backend)
    if backend not in BACKEND_TO_PREFIX:
        return BACKEND_DEFAULT_MODELS.get("ollama", "mistral")  # Fallback for unknown
    return _resolve_model(backend)


def get_litellm_model_for_backend(backend: str) -> str:
    """Get LiteLLM model string for a specific backend (e.g. gemini/gemini-2.0-flash).

    Use when you need the model for a backend without changing LLM_BACKEND,
    e.g. integration tests that validate a specific provider.

    Args:
        backend: Backend name (ollama, openai, anthropic, azure, huggingface, gemini).

    Returns:
        LiteLLM model string like gemini/gemini-2.0-flash.
    """
    backend = _normalize_backend(backend)
    if backend not in BACKEND_TO_PREFIX:
        raise ValueError(f"Unknown backend '{backend}'. Supported: {', '.join(BACKEND_TO_PREFIX)}")
    model = _resolve_model(backend)
    prefix = BACKEND_TO_PREFIX[backend]
    if backend == "azure":
        return model if model.startswith("azure/") else f"azure/{model}"
    return f"{prefix}/{model}"
