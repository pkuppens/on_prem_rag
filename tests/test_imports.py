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

        assert app is not None
        assert start_server is not None
        assert DocumentLoader is not None
    except ImportError as e:
        pytest.fail(
            f"Failed to import RAG pipeline modules: {e}\n\n"
            "FIX: Run 'pip install -e .[dev]' to install the package in development mode.\n"
            "This will make all src.* imports available system-wide."
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
    import sys
    from pathlib import Path

    # Test that the modules referenced in pyproject.toml scripts exist
    script_modules = ["src.auth_service.main", "src.rag_pipeline.file_ingestion", "src.test_app"]

    for module_name in script_modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                pytest.fail(
                    f"Module {module_name} not found.\n\n"
                    "FIX: Run 'pip install -e .[dev]' to install the package in development mode.\n"
                    "This will make all src.* modules discoverable by the Python import system."
                )

            # Try to actually import it
            module = importlib.import_module(module_name)
            assert module is not None

        except ImportError as e:
            pytest.fail(
                f"Failed to import {module_name}: {e}\n\n"
                "FIX: Run 'pip install -e .[dev]' to install the package in development mode.\n"
                "This will resolve all internal module dependencies."
            )
