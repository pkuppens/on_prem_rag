"""Test configuration and fixtures.

This module provides shared fixtures and configuration for all tests.
"""

import os
import shutil
import socket
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path
from urllib.parse import urlparse

import pytest

from src.backend.rag_pipeline.utils.progress import progress_notifier

_MAX_LOCAL_WORKERS = 8  # Leave cores free for OS/IDE; cap memory usage


def pytest_configure(config: pytest.Config) -> None:
    """Configure parallel workers and isolate ChromaDB per worker.

    Worker count: caps xdist ``-n auto`` at _MAX_LOCAL_WORKERS on high-core machines.
    A hardcoded ``-n N`` on the CLI (e.g. ``-n 2`` in CI) is always respected as-is.

    ChromaDB isolation: each worker gets its own CHROMA_PERSIST_DIR so that parallel
    workers never share the same SQLite file (prevents "database is locked" errors).
    """
    # Cap -n auto on the controller process (xdist workers don't have config.option.numprocesses)
    if hasattr(config.option, "numprocesses") and config.option.numprocesses == "auto":
        cpu_count = os.cpu_count() or 1
        config.option.numprocesses = min(cpu_count, _MAX_LOCAL_WORKERS)

    # Isolate ChromaDB per worker (or per main process when not using xdist)
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    chroma_dir = Path(tempfile.gettempdir()) / f"chroma_test_{worker_id}"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CHROMA_PERSIST_DIR"] = str(chroma_dir)


OLLAMA_SKIP_REASON = (
    "Ollama (LLM service) not running on port 11434. "
    "Start with: ollama serve. "
    "These tests require a local LLM for integration validation."
)

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

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
    from backend.shared.utils.directory_utils import get_uploaded_files_dir

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


def _ollama_available() -> bool:
    """Return True if Ollama is reachable (quick socket check).

    Uses OLLAMA_BASE_URL or defaults to localhost:11434.
    """
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 11434
    except Exception:
        host, port = "localhost", 11434
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip internet and ollama tests when connectivity/stack not available."""

    run_internet = config.getoption("--run-internet")
    no_internet = config.getoption("--no-internet")
    if run_internet and not no_internet and _internet_available():
        pass
    elif no_internet or not _internet_available():
        skip_marker = pytest.mark.skip(reason="requires internet access")
        for item in items:
            if "internet" in item.keywords:
                item.add_marker(skip_marker)

    # When ollama tests would run, skip with clear message if Ollama not available.
    ollama_items = [i for i in items if "ollama" in i.keywords]
    if ollama_items and not _ollama_available():
        skip_marker = pytest.mark.skip(reason=OLLAMA_SKIP_REASON)
        for item in ollama_items:
            item.add_marker(skip_marker)
