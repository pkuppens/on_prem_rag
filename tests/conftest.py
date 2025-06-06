"""Pytest configuration and fixtures."""

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the path to the test data directory.

    This directory is version controlled and contains fixed test files.
    """
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def test_temp_dir() -> Path:
    """Return the path to the test temporary directory.

    This directory is gitignored and used for test output.
    """
    return Path(__file__).parent / "test_temp"


@pytest.fixture
def test_case_dir(test_temp_dir) -> Path:
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
