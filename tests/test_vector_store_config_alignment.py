"""Ingestion and query must resolve the same ChromaDB directory.

As a developer running the backend natively, I want uploaded documents to be found by /api/v1/qa,
so the write side (ingestion) and the read side (query orchestrator) must use one store location.
"""

from pathlib import Path

import pytest

from backend.query_service.application.query_orchestrator import QueryOrchestrator
from backend.retrieval.infrastructure.vector_store_config import VectorStoreConfig


def _orchestrator_persist_dir() -> str:
    orchestrator = QueryOrchestrator(completion_service=object())  # LLM not needed for this check
    return orchestrator._retrieval._config["persist_dir"]


def test_query_reads_where_ingestion_writes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """CHROMA_PERSIST_DIR drives both the write config and the orchestrator's retrieval."""
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.delenv("PERSIST_DIRECTORY", raising=False)

    assert Path(VectorStoreConfig().persist_directory) == tmp_path
    assert Path(_orchestrator_persist_dir()) == tmp_path


def test_legacy_persist_directory_alias(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """PERSIST_DIRECTORY still works when CHROMA_PERSIST_DIR is unset, for both sides."""
    monkeypatch.delenv("CHROMA_PERSIST_DIR", raising=False)
    monkeypatch.setenv("PERSIST_DIRECTORY", str(tmp_path))

    assert Path(VectorStoreConfig().persist_directory) == tmp_path
    assert Path(_orchestrator_persist_dir()) == tmp_path
