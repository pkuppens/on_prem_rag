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

    def test_direct_mode_uses_local_processing(self, tmp_path):
        """--direct should invoke local processing function."""
        file_path = tmp_path / "doc.txt"
        file_path.write_text("data")

        with patch("scripts.upload_documents.process_local_file") as mock_local:
            result = upload_documents.main(["--direct", str(file_path)])

        assert result == 0
        mock_local.assert_called_once()

    def test_upload_only_flag(self, tmp_path):
        """--upload-only forwards True to process_local_file."""
        file_path = tmp_path / "doc.txt"
        file_path.write_text("data")

        with patch("scripts.upload_documents.process_local_file") as mock_local:
            upload_documents.main(["--direct", "--upload-only", str(file_path)])

        mock_local.assert_called_once()
        args, _ = mock_local.call_args
        assert args[3] is True

    def test_clear_flag_invokes_cleanup(self, tmp_path):
        """--clear should call backend cleanup."""
        file_path = tmp_path / "doc.txt"
        file_path.write_text("data")

        with patch("scripts.upload_documents.clear_backend") as mock_clear, patch("scripts.upload_documents.process_local_file"):
            upload_documents.main(["--direct", "--clear", str(file_path)])

        mock_clear.assert_called_once()
