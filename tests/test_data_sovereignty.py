"""Tests for the DATA_SOVEREIGNTY_MODE startup guard.

As a compliance officer, I want the system to refuse to start with a cloud LLM
backend when DATA_SOVEREIGNTY_MODE=strict is configured, so that patient/sensitive
data never leaves the on-premises boundary through misconfiguration.
"""

import pytest

from backend.rag_pipeline.config.llm_config import check_data_sovereignty


@pytest.mark.parametrize("cloud_backend", ["openai", "anthropic", "azure", "gemini"])
def test_strict_mode_blocks_cloud_backends(cloud_backend, monkeypatch) -> None:
    """DATA_SOVEREIGNTY_MODE=strict must reject cloud LLM backends at startup."""
    monkeypatch.setenv("DATA_SOVEREIGNTY_MODE", "strict")
    monkeypatch.setenv("LLM_BACKEND", cloud_backend)

    with pytest.raises(RuntimeError, match="DATA_SOVEREIGNTY_MODE=strict"):
        check_data_sovereignty()


def test_strict_mode_allows_ollama(monkeypatch) -> None:
    """DATA_SOVEREIGNTY_MODE=strict must allow the local ollama backend."""
    monkeypatch.setenv("DATA_SOVEREIGNTY_MODE", "strict")
    monkeypatch.setenv("LLM_BACKEND", "ollama")

    check_data_sovereignty()  # Must not raise


def test_permissive_mode_allows_cloud_backends(monkeypatch) -> None:
    """Without DATA_SOVEREIGNTY_MODE=strict, cloud backends must be accepted (default permissive)."""
    monkeypatch.delenv("DATA_SOVEREIGNTY_MODE", raising=False)
    monkeypatch.setenv("LLM_BACKEND", "openai")

    check_data_sovereignty()  # Must not raise


def test_strict_mode_case_insensitive(monkeypatch) -> None:
    """DATA_SOVEREIGNTY_MODE check must be case-insensitive for robustness."""
    monkeypatch.setenv("DATA_SOVEREIGNTY_MODE", "STRICT")
    monkeypatch.setenv("LLM_BACKEND", "anthropic")

    with pytest.raises(RuntimeError):
        check_data_sovereignty()
