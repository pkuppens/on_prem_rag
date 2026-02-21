"""Tests for fetch_healthcare_guidelines script.

As a user I want to download clinical guideline PDFs by reference, so I can ingest
them into the RAG system without storing large binaries in the repo.
Technical: Fetch script downloads PDFs to output dir; idempotent (skips existing).
Validation: Mock httpx; verify file written, skip when exists, error on 404.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scripts import fetch_healthcare_guidelines


class TestFetchHealthcareGuidelines:
    """Unit tests for the fetch_healthcare_guidelines script."""

    def test_fetch_downloads_pdf_to_output_dir(
        self,
        tmp_path: Path,
    ) -> None:
        """As a user I want PDFs downloaded to the output dir, so I can ingest them.
        Technical: fetch_healthcare_guidelines writes PDF content to output_dir/filename.
        Validation: Mock httpx GET; verify file created with correct content.
        """
        source = fetch_healthcare_guidelines.GuidelineSource(
            url="https://example.com/guideline.pdf",
            title="Test guideline",
            filename="test_guideline.pdf",
        )
        pdf_content = b"%PDF-1.4 mock content"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pdf_content
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(fetch_healthcare_guidelines, "httpx") as mock_httpx:
            mock_httpx.Client.return_value = mock_client

            count = fetch_healthcare_guidelines.fetch_healthcare_guidelines(
                sources=[source],
                output_dir=tmp_path,
            )

        assert count == 1
        out_file = tmp_path / "test_guideline.pdf"
        assert out_file.exists()
        assert out_file.read_bytes() == pdf_content
        mock_client.get.assert_called_once_with(
            "https://example.com/guideline.pdf",
            follow_redirects=True,
        )

    def test_fetch_skips_existing_file(
        self,
        tmp_path: Path,
    ) -> None:
        """As a user I want existing files skipped, so re-runs are fast and idempotent.
        Technical: When output file exists, no HTTP request is made.
        Validation: Create file beforehand; verify get() not called.
        """
        source = fetch_healthcare_guidelines.GuidelineSource(
            url="https://example.com/existing.pdf",
            title="Existing",
            filename="existing.pdf",
        )
        (tmp_path / "existing.pdf").write_bytes(b"existing content")

        mock_client = MagicMock()

        with patch.object(fetch_healthcare_guidelines, "httpx") as mock_httpx:
            mock_httpx.Client.return_value = mock_client

            count = fetch_healthcare_guidelines.fetch_healthcare_guidelines(
                sources=[source],
                output_dir=tmp_path,
            )

        assert count == 0
        mock_client.get.assert_not_called()
        assert (tmp_path / "existing.pdf").read_bytes() == b"existing content"

    def test_fetch_handles_http_error(
        self,
        tmp_path: Path,
    ) -> None:
        """As a user I want HTTP errors raised, so I notice broken URLs.
        Technical: 404 or other HTTP errors propagate.
        Validation: Mock raise_for_status to raise HTTPStatusError; expect exception.
        """
        source = fetch_healthcare_guidelines.GuidelineSource(
            url="https://example.com/notfound.pdf",
            title="Not found",
            filename="notfound.pdf",
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404",
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with patch.object(fetch_healthcare_guidelines, "httpx") as mock_httpx:
            mock_httpx.Client.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                fetch_healthcare_guidelines.fetch_healthcare_guidelines(
                    sources=[source],
                    output_dir=tmp_path,
                )

    def test_main_creates_output_dir(
        self,
        tmp_path: Path,
    ) -> None:
        """As a user I want the output dir created if missing, so I need no manual setup.
        Technical: main() ensures output_dir exists before fetching.
        Validation: Use non-existent subdir; verify it exists after run.
        """
        output_dir = tmp_path / "healthcare_guidelines"
        assert not output_dir.exists()

        with patch(
            "scripts.fetch_healthcare_guidelines.fetch_healthcare_guidelines",
            return_value=0,
        ) as mock_fetch:
            fetch_healthcare_guidelines.main(["--output", str(output_dir)])

        assert output_dir.exists()
        mock_fetch.assert_called_once()
        call_output = mock_fetch.call_args[1]["output_dir"]
        assert call_output == output_dir

    def test_default_sources_non_empty(self) -> None:
        """Default NHG source list is non-empty for demo use."""
        sources = fetch_healthcare_guidelines.DEFAULT_NHG_SOURCES
        assert len(sources) >= 8
        for s in sources:
            assert s.url.startswith("https://")
            assert s.filename.endswith(".pdf")
            assert s.title
