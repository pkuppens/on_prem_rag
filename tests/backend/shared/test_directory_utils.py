"""Behaviour of backend.shared.utils.directory_utils.

Tests that need the project root patch ``get_project_root`` to ``tmp_path`` so no test writes into the repo.
"""

from pathlib import Path

import pytest

from backend.shared.utils import directory_utils as du


@pytest.fixture
def fake_root(tmp_path, monkeypatch) -> Path:
    """A project root inside tmp_path, so error messages can show relative paths."""
    monkeypatch.setattr(du, "get_project_root", lambda: tmp_path)
    return tmp_path


def _deny_mkdir(self, *args, **kwargs):
    raise PermissionError("denied")


class TestProjectLayout:
    def test_get_project_root_contains_src_backend(self):
        """As a developer I want the project root to be the parent of ``src``."""
        root = du.get_project_root()

        assert (root / "src" / "backend").is_dir()

    def test_get_project_root_outside_src_tree_raises(self, tmp_path, monkeypatch):
        """If the module is not located under a ``src`` directory, finding the root fails loudly."""
        monkeypatch.setattr(du, "__file__", str(tmp_path / "pkg" / "module.py"))

        with pytest.raises(RuntimeError, match="project root"):
            du.get_project_root()

    @pytest.mark.parametrize(
        ("getter", "expected"),
        [
            (du.get_data_dir, "data"),
            (du.get_chunks_dir, "data/chunks"),
            (du.get_database_dir, "data/database"),
            (du.get_cache_dir, "data/cache"),
            (du.get_uploaded_files_dir, "data/uploads"),
        ],
        ids=["data", "chunks", "database", "cache", "uploads"],
    )
    def test_data_directories_live_under_project_data_dir(self, getter, expected, fake_root, monkeypatch):
        """As an operator I want all data directories under ``<root>/data``."""
        monkeypatch.delenv("UPLOADED_FILES_DIR", raising=False)

        assert getter() == fake_root / expected

    def test_uploaded_files_dir_env_override_wins(self, tmp_path, monkeypatch):
        """As an operator I want UPLOADED_FILES_DIR to redirect uploads (e.g. to a mounted volume)."""
        monkeypatch.setenv("UPLOADED_FILES_DIR", str(tmp_path / "volume"))

        assert du.get_uploaded_files_dir() == tmp_path / "volume"

    def test_test_data_dir_returns_existing_directory(self, fake_root):
        """The test data directory is ``<root>/tests/test_data`` when it exists."""
        (fake_root / "tests" / "test_data").mkdir(parents=True)

        assert du.get_test_data_dir() == fake_root / "tests" / "test_data"

    def test_test_data_dir_missing_raises_with_location(self, fake_root):
        """A missing test data directory is reported with the expected location."""
        with pytest.raises(FileNotFoundError, match="test_data"):
            du.get_test_data_dir()


class TestPathHelpers:
    @pytest.mark.parametrize("bad", [None, 42, 1.5], ids=["none", "int", "float"])
    def test_validate_path_input_rejects_non_path_values(self, bad):
        """Only str and Path are accepted as paths."""
        with pytest.raises(ValueError):
            du._validate_path_input(bad)

    @pytest.mark.parametrize("value", ["some/dir", Path("some/dir")], ids=["str", "path"])
    def test_validate_path_input_returns_path(self, value):
        """str and Path inputs are normalised to Path."""
        assert du._validate_path_input(value) == Path("some/dir")

    def test_get_relative_path_defaults_to_project_root(self, fake_root):
        """Relative paths are computed from the project root unless a base is given."""
        assert du.get_relative_path(fake_root / "a" / "b.txt") == str(Path("a") / "b.txt")

    def test_get_relative_path_uses_explicit_base(self, tmp_path):
        """An explicit base overrides the project root."""
        assert du.get_relative_path(tmp_path / "x" / "y", base=tmp_path / "x") == "y"

    def test_format_path_for_error_prefixes_dot_slash(self, fake_root):
        """Error messages show project-relative paths as ``./relative``."""
        assert du._format_path_for_error(fake_root / "data") == "./data"

    def test_ensure_directory_exists_creates_nested_and_is_idempotent(self, tmp_path):
        """Creating an existing directory again is not an error."""
        target = tmp_path / "a" / "b"

        du.ensure_directory_exists(target)
        du.ensure_directory_exists(target)

        assert target.is_dir()


class TestRequireDirectory:
    def test_existing_directory_is_returned_as_path(self, fake_root):
        """A string path to an existing directory is accepted and returned as Path."""
        assert du.require_directory(str(fake_root)) == fake_root

    def test_file_instead_of_directory_raises_not_a_directory(self, fake_root):
        """A file where a directory is expected is reported, using the description."""
        file = fake_root / "f.txt"
        file.write_text("x")

        with pytest.raises(NotADirectoryError, match="not a upload directory"):
            du.require_directory(file, description="upload directory")

    def test_missing_directory_raises_with_capitalised_description(self, fake_root):
        """A missing directory names itself and its relative path."""
        with pytest.raises(FileNotFoundError, match=r"Upload dir not found: \./missing"):
            du.require_directory(fake_root / "missing", description="upload dir")

    def test_missing_directory_is_not_created(self, fake_root):
        """Requiring a directory never creates it."""
        with pytest.raises(FileNotFoundError):
            du.require_directory(fake_root / "later")

        assert not (fake_root / "later").exists()

    def test_missing_directory_outside_project_root_raises_file_not_found(self, tmp_path):
        """Paths outside the repo (e.g. a mounted volume) yield the normal error, showing the full path."""
        missing = tmp_path / "volume" / "missing"

        with pytest.raises(FileNotFoundError, match="Directory not found"):
            du.require_directory(missing)

    @pytest.mark.parametrize("bad", [None, 5], ids=["none", "int"])
    def test_invalid_path_input_raises_value_error(self, bad):
        """None or non-path input fails before touching the filesystem."""
        with pytest.raises(ValueError):
            du.require_directory(bad)


class TestRequireAccessibleDirectory:
    @pytest.mark.parametrize(
        ("require", "label"),
        [(du.require_readable_directory, "read"), (du.require_writable_directory, "write")],
        ids=["readable", "writable"],
    )
    def test_access_failure_raises_permission_error(self, require, label, fake_root, monkeypatch):
        """A directory the process may not read/write is rejected."""
        monkeypatch.setattr(du.os, "access", lambda *_: False)

        with pytest.raises(PermissionError, match=f"No {label} permission"):
            require(fake_root)

    @pytest.mark.parametrize(
        "require",
        [du.require_readable_directory, du.require_writable_directory],
        ids=["readable", "writable"],
    )
    def test_accessible_directory_is_returned(self, require, fake_root):
        """A normal temp directory is readable and writable."""
        assert require(fake_root) == fake_root

    @pytest.mark.parametrize(
        "require",
        [du.require_readable_directory, du.require_writable_directory],
        ids=["readable", "writable"],
    )
    def test_missing_directory_raises_file_not_found(self, require, fake_root):
        """Existence is checked before access."""
        with pytest.raises(FileNotFoundError):
            require(fake_root / "missing")


class TestRequireEmptyDirectory:
    def test_non_empty_directory_raises(self, fake_root):
        """A directory that contains anything is rejected."""
        (fake_root / "child.txt").write_text("x")

        with pytest.raises(du.DirectoryEmptyError, match="is not empty"):
            du.require_empty_directory(fake_root)

    def test_empty_directory_is_returned(self, fake_root):
        """An empty directory passes."""
        empty = fake_root / "empty"
        empty.mkdir()

        assert du.require_empty_directory(empty) == empty

    def test_missing_directory_raises_file_not_found(self, fake_root):
        """A missing directory is an error, not 'empty'."""
        with pytest.raises(FileNotFoundError):
            du.require_empty_directory(fake_root / "absent")


class TestEnsureDirectory:
    def test_creates_nested_directories_by_default(self, fake_root):
        """Parents are created unless told otherwise."""
        target = fake_root / "a" / "b" / "c"

        assert du.ensure_directory(target) == target
        assert target.is_dir()

    def test_existing_directory_is_accepted(self, fake_root):
        """Ensuring an existing directory is a no-op that returns the path."""
        assert du.ensure_directory(fake_root) == fake_root

    def test_file_in_the_way_raises_not_a_directory(self, fake_root):
        """A file at the target path is reported rather than overwritten."""
        file = fake_root / "f"
        file.write_text("x")

        with pytest.raises(NotADirectoryError, match="not a directory"):
            du.ensure_directory(file)

    def test_missing_parent_without_create_parents_raises(self, fake_root):
        """create_parents=False does not create missing parents."""
        with pytest.raises(FileNotFoundError):
            du.ensure_directory(fake_root / "no" / "parent", create_parents=False)

    def test_permission_denied_is_wrapped_with_location(self, fake_root, monkeypatch):
        """A denied mkdir explains where and why."""
        monkeypatch.setattr(Path, "mkdir", _deny_mkdir)

        with pytest.raises(PermissionError, match=r"Cannot create or access cache at \./blocked"):
            du.ensure_directory(fake_root / "blocked", description="cache")

    @pytest.mark.parametrize("bad", [None, 3], ids=["none", "int"])
    def test_invalid_path_input_raises_value_error(self, bad):
        """None or non-path input is rejected."""
        with pytest.raises(ValueError):
            du.ensure_directory(bad)


class TestEnsureWritableDirectory:
    def test_creates_missing_directory_and_returns_it(self, fake_root):
        """A missing directory (with parents) is created and usable."""
        target = fake_root / "x" / "y"

        assert du.ensure_writable_directory(target, description="index storage directory") == target
        assert target.is_dir()

    def test_existing_directory_is_accepted(self, fake_root):
        """An existing writable directory is returned unchanged."""
        assert du.ensure_writable_directory(fake_root) == fake_root

    def test_not_writable_directory_raises_permission_error(self, fake_root, monkeypatch):
        """A directory that exists but cannot be written to is rejected after creation."""
        monkeypatch.setattr(du.os, "access", lambda *_: False)

        with pytest.raises(PermissionError, match="No write permission for index dir"):
            du.ensure_writable_directory(fake_root, description="index dir")

    def test_create_failure_is_reported_as_permission_error(self, fake_root, monkeypatch):
        """If creating the directory is denied, the error explains where and why."""
        monkeypatch.setattr(Path, "mkdir", _deny_mkdir)

        with pytest.raises(PermissionError, match=r"Cannot create or access directory at \./nope"):
            du.ensure_writable_directory(fake_root / "nope")
