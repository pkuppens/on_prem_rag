"""Pytest configuration and fixtures."""

import shutil
import socket
import uuid
from collections.abc import Generator
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
    if run_internet and _internet_available():
        return

    skip_marker = pytest.mark.skip(reason="requires internet access")
    for item in items:
        if "requires_internet" in item.keywords:
            item.add_marker(skip_marker)
