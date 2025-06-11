"""Utility functions for directory validation and handling."""

import os
from pathlib import Path
from typing import Optional


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
    return f"./{get_relative_path(path)}"


def validate_directory(
    path: str | Path | None,
    must_exist: bool = True,
    must_be_empty: bool = False,
    must_be_writable: bool = False,
    must_be_readable: bool = False,
    create_if_missing: bool = False,
    description: str = "directory",
) -> Path:
    """
    Validate a directory against various criteria.

    Args:
        path: Path to validate
        must_exist: Whether the directory must exist
        must_be_empty: Whether the directory must be empty
        must_be_writable: Whether the directory must be writable
        must_be_readable: Whether the directory must be readable
        create_if_missing: Whether to create the directory if it doesn't exist
        description: Description of the directory for error messages

    Returns:
        Path object of the validated directory

    Raises:
        ValueError: If path is None or invalid type
        FileNotFoundError: If directory doesn't exist and must_exist is True
        NotADirectoryError: If path exists but is not a directory
        DirectoryEmptyError: If directory is empty and must_be_empty is True
        PermissionError: If directory access checks fail

    """
    path = _validate_path_input(path)

    # Check if path exists
    if path.exists():
        if not path.is_dir():
            raise NotADirectoryError(
                f"Path exists but is not a {description}: {_format_path_for_error(path)}\nPlease provide a valid directory path."
            )
    elif must_exist:
        if create_if_missing:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionError(
                    f"Cannot create {description} at {_format_path_for_error(path)}\n"
                    f"Permission denied: {e!s}\n"
                    "Please check your permissions or choose a different location."
                ) from e
        else:
            raise FileNotFoundError(
                f"{description.capitalize()} not found: {_format_path_for_error(path)}\n"
                "Please create this directory or provide a valid path."
            )

    # Check if directory is empty
    if must_be_empty and any(path.iterdir()):
        raise DirectoryEmptyError(
            f"{description.capitalize()} is not empty: {_format_path_for_error(path)}\nPlease provide an empty directory."
        )

    # Check permissions
    if must_be_writable and not os.access(path, os.W_OK):
        raise PermissionError(
            f"No write permission for {description}: {_format_path_for_error(path)}\n"
            "Please check your permissions or choose a different location."
        )

    if must_be_readable and not os.access(path, os.R_OK):
        raise PermissionError(
            f"No read permission for {description}: {_format_path_for_error(path)}\n"
            "Please check your permissions or choose a different location."
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
