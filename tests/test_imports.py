"""
Test module imports to ensure proper package configuration.

This test verifies that all modules can be imported correctly.
If this test fails, it indicates a package configuration issue.
"""

import pytest


def test_auth_service_imports():
    """Test that auth service modules can be imported."""
    try:
        from src.auth_service.database import init_db
        from src.auth_service.main import app, start_server
        from src.auth_service.models import Session, User

        assert app is not None
        assert start_server is not None
        assert User is not None
        assert Session is not None
        assert init_db is not None
    except ImportError as e:
        pytest.fail(
            f"Failed to import auth service modules: {e}\n\n"
            "FIX: Run 'pip install -e .[dev]' to install the package in development mode.\n"
            "This will make all src.* imports available system-wide."
        )


def test_rag_pipeline_imports():
    """Test that RAG pipeline modules can be imported."""
    try:
        from src.rag_pipeline.core.document_loader import DocumentLoader
        from src.rag_pipeline.file_ingestion import app, start_server
        from src.rag_pipeline.utils.directory_utils import get_uploaded_files_dir

        # Verify uploaded_files directory exists
        uploaded_files_dir = get_uploaded_files_dir()
        assert uploaded_files_dir.exists(), (
            f"Uploaded files directory not found at {uploaded_files_dir}\n"
            "This directory should be created by the FastAPI app initialization."
        )

        assert app is not None, "FastAPI app should be initialized"
        assert start_server is not None, "start_server function should be available"
        assert DocumentLoader is not None, "DocumentLoader class should be available"
    except ImportError as e:
        pytest.fail(
            f"Failed to import RAG pipeline modules: {e}\n\n"
            "FIX: Run 'pip install -e .[dev]' to install the package in development "
            "mode.\nThis will make all src.* imports available system-wide."
        )
    except Exception as e:
        pytest.fail(
            f"Unexpected error during RAG pipeline import test: {e}\n\n"
            "This could be due to missing directories or permissions issues.\n"
            "Please ensure the 'uploaded_files' directory exists and is writable."
        )


def test_test_app_imports():
    """Test that test app modules can be imported."""
    try:
        from src.test_app import app, start_server

        assert app is not None
        assert start_server is not None
    except ImportError as e:
        pytest.fail(
            f"Failed to import test app modules: {e}\n\n"
            "FIX: Run 'pip install -e .[dev]' to install the package in development mode.\n"
            "This will make all src.* imports available system-wide."
        )


def test_scripts_can_be_called():
    """Test that entry point scripts can be imported without errors."""
    import importlib.util

    from src.rag_pipeline.utils.directory_utils import get_uploaded_files_dir

    # Verify uploaded_files directory exists
    uploaded_files_dir = get_uploaded_files_dir()
    assert uploaded_files_dir.exists(), (
        f"Uploaded files directory not found at {uploaded_files_dir}\n"
        "This directory should be created by the FastAPI app initialization."
    )

    # Test that the modules referenced in pyproject.toml scripts exist
    script_modules = ["src.auth_service.main", "src.rag_pipeline.file_ingestion", "src.test_app"]

    for module_name in script_modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                pytest.fail(
                    f"Module {module_name} not found.\n\n"
                    "FIX: Run 'pip install -e .[dev]' to install the package in development "
                    "mode.\nThis will make all src.* modules discoverable by the Python "
                    "import system."
                )

            # Try to actually import it
            module = importlib.import_module(module_name)
            assert module is not None, f"Module {module_name} should be importable"

        except ImportError as e:
            pytest.fail(
                f"Failed to import {module_name}: {e}\n\n"
                "FIX: Run 'pip install -e .[dev]' to install the package in development "
                "mode.\nThis will resolve all internal module dependencies."
            )
        except Exception as e:
            pytest.fail(
                f"Unexpected error importing {module_name}: {e}\n\n"
                "This could be due to missing directories or permissions issues.\n"
                "Please ensure the 'uploaded_files' directory exists and is writable."
            )
