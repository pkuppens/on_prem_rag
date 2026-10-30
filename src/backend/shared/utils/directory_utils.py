"""Utility functions for directory validation and handling.

This module provides functions for managing the project's directory structure
as documented in docs/PROJECT_STRUCTURE.md. All data directories are organized
under the main /data/ directory which is gitignored for privacy protection.

Lives in backend.shared so auth_service, memory, and wbso can use it without
depending on rag_pipeline.
"""

import os
from pathlib import Path


class DirectoryError(Exception):
    """Base exception for directory-related errors."""


class DirectoryEmptyError(DirectoryError):
    """Raised when a directory is empty but should not be."""


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root directory
    """
    # Start from the current file and go up until we find the project root
    current_path = Path(__file__).resolve()
    while current_path.name != "src":
        if current_path.parent == current_path:  # Reached root of filesystem
            raise RuntimeError("Could not find project root directory")
        current_path = current_path.parent
    return current_path.parent


def get_data_dir() -> Path:
    """
    Get the main data directory.

    Returns:
        Path to the data directory
    """
    return get_project_root() / "data"


def get_uploaded_files_dir() -> Path:
    """
    Get the uploaded files directory.

    Returns:
        Path to the uploaded files directory
    """
    override = os.getenv("UPLOADED_FILES_DIR")
    if override:
        return Path(override)
    return get_data_dir() / "uploads"


def get_chunks_dir() -> Path:
    """
    Get the chunks directory.

    Returns:
        Path to the chunks directory
    """
    return get_data_dir() / "chunks"


def get_database_dir() -> Path:
    """
    Get the database directory.

    Returns:
        Path to the database directory
    """
    return get_data_dir() / "database"


def get_cache_dir() -> Path:
    """
    Get the cache directory.

    Returns:
        Path to the cache directory
    """
    return get_data_dir() / "cache"


def get_test_data_dir() -> Path:
    """
    Get the test data directory.

    Returns:
        Path to the test data directory

    Raises:
        FileNotFoundError: If test data directory cannot be found
    """
    root = get_project_root()
    test_data = root / "tests" / "test_data"

    if not test_data.exists():
        raise FileNotFoundError(f"Test data directory not found at expected location: {test_data}")

    return test_data


def _validate_path_input(path: str | Path | None) -> Path:
    """
    Validate and convert path input to Path object.

    Args:
        path: Input path to validate

    Returns:
        Path object

    Raises:
        ValueError: If path is None or invalid type

    """
    if path is None:
        raise ValueError("Path cannot be None")
    if not isinstance(path, str | Path):
        raise ValueError(f"Path must be str or Path, got {type(path)}")
    return Path(path)


def _format_path_for_error(path: Path) -> str:
    """
    Format a path for error messages, showing the relative path from project root.

    Args:
        path (Path): Path to format

    Returns:
        str: Formatted path string
    """
    try:
        return f"./{get_relative_path(path)}"
    except ValueError:  # outside the project root (e.g. a mounted volume): show the full path
        return str(path)


def require_directory(path: str | Path | None, description: str = "directory") -> Path:
    """
    Require that a directory exists. Nothing is created or modified.

    Args:
        path: Path to check
        description: Description of the directory for error messages

    Returns:
        Path object of the existing directory

    Raises:
        ValueError: If path is None or invalid type
        FileNotFoundError: If the path does not exist
        NotADirectoryError: If the path exists but is not a directory
    """
    path = _validate_path_input(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{description.capitalize()} not found: {_format_path_for_error(path)}\n"
            "Please create this directory or provide a valid path."
        )
    if not path.is_dir():
        raise NotADirectoryError(
            f"Path exists but is not a {description}: {_format_path_for_error(path)}\nPlease provide a valid directory path."
        )
    return path


def _require_access(path: Path, mode: int, action: str, description: str) -> Path:
    if not os.access(path, mode):
        raise PermissionError(
            f"No {action} permission for {description}: {_format_path_for_error(path)}\n"
            "Please check your permissions or choose a different location."
        )
    return path


def require_readable_directory(path: str | Path | None, description: str = "directory") -> Path:
    """Require an existing directory that the current process can read.

    Raises:
        ValueError, FileNotFoundError, NotADirectoryError: see `require_directory`
        PermissionError: If the directory is not readable
    """
    return _require_access(require_directory(path, description), os.R_OK, "read", description)


def require_writable_directory(path: str | Path | None, description: str = "directory") -> Path:
    """Require an existing directory that the current process can write to.

    Raises:
        ValueError, FileNotFoundError, NotADirectoryError: see `require_directory`
        PermissionError: If the directory is not writable
    """
    return _require_access(require_directory(path, description), os.W_OK, "write", description)


def require_empty_directory(path: str | Path | None, description: str = "directory") -> Path:
    """Require an existing directory without any entries.

    Raises:
        ValueError, FileNotFoundError, NotADirectoryError: see `require_directory`
        DirectoryEmptyError: If the directory contains anything (named for the check; raised when NOT empty)
    """
    path = require_directory(path, description)
    if any(path.iterdir()):
        raise DirectoryEmptyError(
            f"{description.capitalize()} is not empty: {_format_path_for_error(path)}\nPlease provide an empty directory."
        )
    return path


def ensure_directory(
    path: str | Path | None,
    description: str = "directory",
    create_parents: bool = True,
) -> Path:
    """
    Ensure a directory exists and is accessible.

    Args:
        path: Path to ensure
        description: Description of the directory for error messages
        create_parents: Whether to create parent directories if they don't exist

    Returns:
        Path object of the ensured directory

    Raises:
        ValueError: If path is None or invalid type
        PermissionError: If directory cannot be created or accessed
        NotADirectoryError: If path exists but is not a directory

    """
    path = _validate_path_input(path)

    try:
        if path.exists() and not path.is_dir():
            raise NotADirectoryError(
                f"Path exists but is not a {description}: {_format_path_for_error(path)}\nPlease provide a valid directory path."
            )
        path.mkdir(parents=create_parents, exist_ok=True)
        return path
    except PermissionError as e:
        raise PermissionError(
            f"Cannot create or access {description} at {_format_path_for_error(path)}\n"
            f"Permission denied: {e!s}\n"
            "Please check your permissions or choose a different location."
        ) from e


def ensure_writable_directory(path: str | Path | None, description: str = "directory") -> Path:
    """Ensure a directory exists (creating it and its parents) and can be written to.

    Raises:
        ValueError, NotADirectoryError, PermissionError: see `ensure_directory`
        PermissionError: If the directory exists but is not writable
    """
    return _require_access(ensure_directory(path, description), os.W_OK, "write", description)


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        directory (Path): Directory to ensure exists
    """
    directory.mkdir(parents=True, exist_ok=True)


def get_relative_path(path: Path, base: Path | None = None) -> str:
    """
    Get the relative path from the base directory.

    Args:
        path (Path): Path to get relative path for
        base (Optional[Path]): Base directory to get relative path from. Defaults to project root.

    Returns:
        str: Relative path as string
    """
    if base is None:
        base = get_project_root()
    return str(path.relative_to(base))
