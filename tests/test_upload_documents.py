"""Tests for the upload_documents CLI script."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from scripts import upload_documents


class TestUploadDocuments:
    """Unit tests for the CLI upload script."""

    def test_build_upload_name_modes(self, tmp_path):
        """Verify upload name generation for each mode."""
        file_path = tmp_path / "doc.txt"
        file_path.write_text("data")
        base = tmp_path

        assert upload_documents.build_upload_name(file_path, "fullpath", base) == str(file_path.resolve())
        assert upload_documents.build_upload_name(file_path, "filenameonly", base) == "doc.txt"
        assert upload_documents.build_upload_name(file_path, "relativepath", base) == "doc.txt"

    def test_main_uploads_files(self, tmp_path):
        """Upload routine posts files with expected names."""
        file_path = tmp_path / "doc.txt"
        file_path.write_text("data")

        with patch("scripts.upload_documents.upload_file") as mock_upload:
            args = [str(file_path)]
            result = upload_documents.main(args)

        assert result == 0
        mock_upload.assert_called_once()

    def test_haltonerror_stops(self, tmp_path):
        """When --haltonerror is used, errors propagate."""
        file_path = tmp_path / "bad.txt"
        file_path.write_text("data")

        with patch(
            "scripts.upload_documents.upload_file",
            side_effect=upload_documents.UploadError("err"),
        ):
            with pytest.raises(upload_documents.UploadError):
                upload_documents.main(["--haltonerror", str(file_path)])
