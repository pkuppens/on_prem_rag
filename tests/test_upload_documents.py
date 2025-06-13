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

    def test_iter_files_recursion_and_filter(self, tmp_path):
        """Ensure recursion and filtering work and symlinks do not loop."""
        (tmp_path / "a").mkdir()
        sub = tmp_path / "a" / "sub"
        sub.mkdir(parents=True)
        file1 = sub / "f1.txt"
        file1.write_text("x")
        file2 = tmp_path / "a" / "f2.md"
        file2.write_text("y")
        # symlink pointing to parent to create potential loop
        (sub / "link").symlink_to(tmp_path / "a")

        files = list(upload_documents.iter_files([tmp_path], recurse=True, filters={"txt"}))
        assert file1 in files and file2 not in files

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
