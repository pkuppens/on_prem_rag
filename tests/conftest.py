"""Test configuration and fixtures.

This module provides shared fixtures and configuration for all tests.
"""

import os
import shutil
import socket
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from src.backend.rag_pipeline.utils.progress_notifier import progress_notifier

# Ensure test data directory exists
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the path to the test data directory."""
    return TEST_DATA_DIR


@pytest.fixture(autouse=True)
def cleanup_upload_progress():
    """Clean up upload progress tracking before and after each test."""
    # Clear progress tracking before test
    progress_notifier._current_progress.clear()
    yield
    # Clear progress tracking after test
    progress_notifier._current_progress.clear()


@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """Clean up uploaded files before and after each test."""
    from src.backend.rag_pipeline.utils.directory_utils import get_uploaded_files_dir

    uploaded_dir = get_uploaded_files_dir()

    # Create directory if it doesn't exist
    uploaded_dir.mkdir(parents=True, exist_ok=True)

    # Clean up before test
    for file in uploaded_dir.glob("*"):
        if file.is_file():
            file.unlink()

    yield

    # Clean up after test
    for file in uploaded_dir.glob("*"):
        if file.is_file():
            file.unlink()


@pytest.fixture(scope="session")
def test_temp_dir() -> Path:
    """Return the path to the test temporary directory.

    This directory is gitignored and used for test output.
    """
    return Path(__file__).parent / "test_temp"


@pytest.fixture(scope="class")
def test_case_dir(test_temp_dir) -> Generator[Path]:
    """Create and return a unique directory for a test case.

    The directory is automatically cleaned up after the test.
    """
    # Create a unique directory for this test case
    case_dir = test_temp_dir / str(uuid.uuid4())
    case_dir.mkdir(parents=True, exist_ok=True)

    yield case_dir

    # Cleanup after test
    if case_dir.exists():
        shutil.rmtree(case_dir, ignore_errors=True)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom command line options."""

    parser.addoption(
        "--run-internet",
        action="store_true",
        default=False,
        help="Run tests that require internet access",
    )
    parser.addoption(
        "--no-internet",
        action="store_true",
        default=False,
        help="Skip internet tests regardless of connectivity",
    )


def _internet_available() -> bool:
    """Return True if the environment appears to have internet access."""

    try:
        socket.gethostbyname("huggingface.co")
    except OSError:
        return False
    return True


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip internet tests when no connectivity or flag is set."""

    run_internet = config.getoption("--run-internet")
    no_internet = config.getoption("--no-internet")
    if run_internet and not no_internet and _internet_available():
        return

    if no_internet or not _internet_available():
        skip_marker = pytest.mark.skip(reason="requires internet access")
        for item in items:
            if "internet" in item.keywords:
                item.add_marker(skip_marker)
