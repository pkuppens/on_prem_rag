import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth_service.database import Base
from auth_service.main import app, get_db, get_password_hash
from auth_service.models import User


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary database for each test."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Create engine and session for test database
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(bind=test_engine, autoflush=False)

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Override the get_db dependency
    def override_get_db():
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield test_session_local

    # Cleanup
    app.dependency_overrides.clear()

    # Properly close the engine before trying to delete the file
    test_engine.dispose()

    # Try to remove the file, but don't fail if Windows is still holding it
    try:
        os.unlink(db_path)
    except (PermissionError, FileNotFoundError):
        # On Windows, the file might still be locked - this is OK for temp files
        pass


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with isolated database."""
    return TestClient(app)

