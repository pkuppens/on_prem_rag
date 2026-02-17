"""Tests for POST /api/documents/from-url endpoint.

This module tests document ingestion via URL without requiring a running
backend or external HTTP services. All network calls are mocked.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.rag_pipeline.api.app import app


@pytest.fixture
def tmp_upload_dir(tmp_path):
    """Provide a temporary upload directory and monkeypatch documents module."""
    return tmp_path


@pytest.fixture
def client():
    """Provide a TestClient for the app."""
    return TestClient(app)


class TestDocumentsFromUrl:
    """Tests for POST /api/documents/from-url endpoint."""

    @patch("backend.rag_pipeline.api.documents.process_document_background")
    @patch("backend.rag_pipeline.api.documents.httpx.AsyncClient")
    def test_from_url_success_downloads_and_starts_processing(
        self,
        mock_async_client_class,
        mock_process_background,
        client,
        tmp_upload_dir,
        monkeypatch,
    ):
        """As a user I want to provide documents via URL, so I can ingest without local files.
        Technical: POST /api/documents/from-url downloads content and starts background processing.
        Validation: Mock httpx; verify 200, filename saved, background task enqueued.
        """
        monkeypatch.setattr(
            "backend.rag_pipeline.api.documents.uploaded_files_dir",
            tmp_upload_dir,
        )

        # Mock async HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4 test content"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        resp = client.post(
            "/api/documents/from-url",
            json={"url": "https://example.com/doc.pdf"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "downloaded"
        assert data["processing"] == "started"
        assert "file_id" in data
        assert data["file_id"] == "doc.pdf"

        # File should be saved
        saved_file = tmp_upload_dir / "doc.pdf"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"%PDF-1.4 test content"

        # Background task should be queued (runs sync in TestClient)
        mock_process_background.assert_called_once()

    @patch("backend.rag_pipeline.api.documents.process_document_background")
    @patch("backend.rag_pipeline.api.documents.httpx.AsyncClient")
    def test_from_url_uses_content_disposition_filename(
        self,
        mock_async_client_class,
        mock_process_background,
        client,
        tmp_upload_dir,
        monkeypatch,
    ):
        """As a user I want correct filenames when URLs lack extension, so files are named properly.
        Technical: Content-Disposition header overrides path-derived filename.
        """
        monkeypatch.setattr(
            "backend.rag_pipeline.api.documents.uploaded_files_dir",
            tmp_upload_dir,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"plain text content"
        mock_response.headers = {"content-disposition": 'attachment; filename="report-2024.pdf"'}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        resp = client.post(
            "/api/documents/from-url",
            json={"url": "https://example.com/download?id=123"},
        )

        assert resp.status_code == 200
        assert resp.json()["file_id"] == "report-2024.pdf"
        assert (tmp_upload_dir / "report-2024.pdf").exists()

    @patch("backend.rag_pipeline.api.documents.httpx.AsyncClient")
    def test_from_url_rejects_non_http_scheme(
        self,
        mock_async_client_class,
        client,
    ):
        """As a user I want URLs validated for security, so file:// and other schemes are rejected.
        Technical: Only http and https schemes accepted.
        """
        resp = client.post(
            "/api/documents/from-url",
            json={"url": "file:///etc/passwd"},
        )
        assert resp.status_code == 422  # Pydantic HttpUrl validates scheme

    def test_from_url_requires_valid_url(self, client):
        """As a user I want validation of URL format, so malformed requests fail clearly."""
        resp = client.post(
            "/api/documents/from-url",
            json={"url": "not-a-valid-url"},
        )
        assert resp.status_code == 422

    @patch("backend.rag_pipeline.api.documents.httpx.AsyncClient")
    def test_from_url_download_failure_returns_502(
        self,
        mock_async_client_class,
        client,
        tmp_upload_dir,
        monkeypatch,
    ):
        """As a user I want clear errors when download fails, so I can fix the URL.
        Technical: HTTP errors (404, 500) return 502 with download failure message.
        """
        monkeypatch.setattr(
            "backend.rag_pipeline.api.documents.uploaded_files_dir",
            tmp_upload_dir,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        def raise_status_error():
            raise httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response,
            )

        mock_response.raise_for_status = MagicMock(side_effect=raise_status_error)

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        resp = client.post(
            "/api/documents/from-url",
            json={"url": "https://example.com/missing.pdf"},
        )

        assert resp.status_code == 502
        assert "download" in resp.json().get("detail", "").lower() or "failed" in resp.json().get("detail", "").lower()

    @patch("backend.rag_pipeline.api.documents.httpx.AsyncClient")
    def test_from_url_rejects_oversized_document(
        self,
        mock_async_client_class,
        client,
        tmp_upload_dir,
        monkeypatch,
    ):
        """As a user I want size limits on downloaded documents, so the server stays protected.
        Technical: Documents over 50MB return 400.
        """
        monkeypatch.setattr(
            "backend.rag_pipeline.api.documents.uploaded_files_dir",
            tmp_upload_dir,
        )

        # Create content > 50MB
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"x" * (51 * 1024 * 1024)
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        resp = client.post(
            "/api/documents/from-url",
            json={"url": "https://example.com/large.pdf"},
        )

        assert resp.status_code == 400
        assert "50MB" in resp.json().get("detail", "")
