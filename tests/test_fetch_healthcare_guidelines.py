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

            result = fetch_healthcare_guidelines.fetch_healthcare_guidelines(
                sources=[source],
                output_dir=tmp_path,
            )

        assert len(result.downloaded) == 1
        assert result.downloaded[0] == "test_guideline.pdf"
        assert result.skipped == 0
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

            result = fetch_healthcare_guidelines.fetch_healthcare_guidelines(
                sources=[source],
                output_dir=tmp_path,
            )

        assert len(result.downloaded) == 0
        assert result.skipped == 1
        assert result.skipped_files == ("existing.pdf",)
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

        result = fetch_healthcare_guidelines.FetchResult(
            output_dir=output_dir,
            downloaded=(),
            skipped=0,
            skipped_files=(),
        )
        with patch(
            "scripts.fetch_healthcare_guidelines.fetch_healthcare_guidelines",
            return_value=result,
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

    def test_main_prints_success_report(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """As a user I want a success summary after fetch, so I know what was done.
        Technical: main() prints location, downloaded/skipped counts, file list if < 10.
        Validation: Run with mocked fetch returning 2 downloads; verify output.
        """
        result = fetch_healthcare_guidelines.FetchResult(
            output_dir=tmp_path,
            downloaded=("NHG_Urineweginfecties.pdf", "NHG_Depressie.pdf"),
            skipped=1,
            skipped_files=("NHG_Maagklachten.pdf",),
        )
        (tmp_path / "NHG_Urineweginfecties.pdf").write_bytes(b"x" * 500)
        (tmp_path / "NHG_Depressie.pdf").write_bytes(b"y" * 1200)

        with patch(
            "scripts.fetch_healthcare_guidelines.fetch_healthcare_guidelines",
            return_value=result,
        ):
            fetch_healthcare_guidelines.main(["--output", str(tmp_path)])

        out = capsys.readouterr().out
        assert "Location:" in out
        assert "Downloaded: 2 file(s)" in out
        assert "Skipped: 1" in out
        assert "NHG_Urineweginfecties.pdf" in out
        assert "NHG_Depressie.pdf" in out

    def test_success_report_when_all_already_present(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """As a user I want to know when all expected files are already present.
        Technical: Report "All N expected files already present" with list.
        Validation: Mock fetch returning all 11 skipped; verify message and file list.
        """
        sources = fetch_healthcare_guidelines.DEFAULT_NHG_SOURCES
        skipped = tuple(s.filename for s in sources)
        for f in skipped:
            (tmp_path / f).write_bytes(b"x" * 100)

        result = fetch_healthcare_guidelines.FetchResult(
            output_dir=tmp_path,
            downloaded=(),
            skipped=len(skipped),
            skipped_files=skipped,
        )
        with patch(
            "scripts.fetch_healthcare_guidelines.fetch_healthcare_guidelines",
            return_value=result,
        ):
            fetch_healthcare_guidelines.main(
                ["--output", str(tmp_path)],
            )

        out = capsys.readouterr().out
        assert "Location:" in out
        assert "All 11 expected files already present" in out
        assert "11 files" in out
