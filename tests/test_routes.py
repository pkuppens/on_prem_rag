"""Tests for API routes in the RAG pipeline.

This module tests the various API endpoints and their functionality.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.rag_pipeline.api.app import app
from src.backend.rag_pipeline.utils.directory_utils import get_uploaded_files_dir

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test the health check endpoint."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_documents_list(tmp_path, monkeypatch) -> None:
    """Test the document listing endpoint."""
    file_path = tmp_path / "example.txt"
    file_path.write_text("data")
    monkeypatch.setattr("src.backend.rag_pipeline.api.documents.uploaded_files_dir", tmp_path)
    resp = client.get("/api/documents/list")
    assert resp.status_code == 200
    assert resp.json()["files"] == ["example.txt"]
