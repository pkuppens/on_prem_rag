"""Utility functions for directory validation and handling."""

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
    # src\rag_pipeline\utils\directory_utils.py
    return Path(__file__).parent.parent.parent.parent


def get_uploaded_files_dir() -> Path:
    """
    Get the uploaded files directory.

    Returns:
        Path to the uploaded files directory

    Note:
        This directory is used by the FastAPI app to store uploaded files.
        It should be created before the app starts.
    """
    return get_project_root() / "uploaded_files"


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
    Format a path for error messages, using relative paths when possible.

    Args:
        path: Path to format

    Returns:
        Formatted path string
    """
    try:
        # Try to get relative path from project root
        rel_path = path.relative_to(get_project_root())
        return f"./{rel_path}"
    except ValueError:
        # If path is not under project root, just use the name
        return path.name


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
