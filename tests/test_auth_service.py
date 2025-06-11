import os
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("httpx")
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


def test_passwords_are_hashed_in_database(client, test_db) -> None:
    """Test that passwords are stored as hashes, not plain text, in the database."""
    plain_password = "my_secret_password_123"
    username = "hash_test_user"

    # Register a user
    resp = client.post("/register", json={"username": username, "email": "hashtest@example.com", "password": plain_password})
    assert resp.status_code == 200

    # Directly query the database to inspect stored password
    db = test_db()
    user = db.query(User).filter(User.username == username).first()

    # Verify the password_hash is stored, not the plain password
    assert user is not None
    assert user.password_hash is not None
    assert user.password_hash != plain_password  # Plain password should NOT be stored

    # Verify it's actually a SHA-256 hash (64 hex characters)
    assert len(user.password_hash) == 64  # SHA-256 produces 64 hex characters
    assert all(c in "0123456789abcdef" for c in user.password_hash.lower())  # Only hex characters

    # Verify the hash matches what our hashing function produces
    expected_hash = get_password_hash(plain_password)
    assert user.password_hash == expected_hash

    # Verify login still works with the plain password
    login_resp = client.post("/login", json={"username": username, "password": plain_password})
    assert login_resp.status_code == 200

    # Verify login fails with the hash (proves we're not storing plain text)
    login_with_hash_resp = client.post("/login", json={"username": username, "password": user.password_hash})
    assert login_with_hash_resp.status_code == 401

    db.close()


def test_password_hash_consistency(client) -> None:
    """Test that the same password always produces the same hash."""
    password = "consistent_password"

    # Generate multiple hashes of the same password
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    hash3 = get_password_hash(password)

    # All hashes should be identical (SHA-256 is deterministic)
    assert hash1 == hash2 == hash3

    # Different passwords should produce different hashes
    different_hash = get_password_hash("different_password")
    assert hash1 != different_hash


def test_register_user(client) -> None:
    """Test user registration works correctly."""
    resp = client.post("/register", json={"username": "alice", "email": "a@example.com", "password": "secret"})
    assert resp.status_code == 200, f"Registration failed: {resp.text}"

    user_data = resp.json()
    assert user_data["username"] == "alice"
    assert user_data["email"] == "a@example.com"
    assert "password" not in user_data  # Password should not be returned


def test_register_and_login(client) -> None:
    """Test complete authentication flow."""
    resp = client.post("/register", json={"username": "bob", "email": "b@example.com", "password": "secret"})
    assert resp.status_code == 200, f"Registration failed: {resp.text}"

    token_resp = client.post("/login", json={"username": "bob", "password": "secret"})
    assert token_resp.status_code == 200, f"Login failed: {token_resp.text}"

    token = token_resp.json()["token"]
    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, f"User info failed: {me.text}"
    assert me.json()["username"] == "bob"


def test_register_duplicate_username(client) -> None:
    """Test that duplicate usernames are rejected."""
    # First registration should succeed
    resp = client.post("/register", json={"username": "duplicate", "email": "d1@example.com", "password": "secret"})
    assert resp.status_code == 200, f"First registration failed: {resp.text}"

    # Second registration with same username should fail
    resp = client.post("/register", json={"username": "duplicate", "email": "d2@example.com", "password": "secret"})
    assert resp.status_code == 400
    assert "Username already" in resp.json()["detail"]


def test_login_invalid_credentials(client) -> None:
    """Test that invalid login credentials are rejected."""
    resp = client.post("/login", json={"username": "nonexistent", "password": "wrong"})
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_me_without_token(client) -> None:
    """Test that /me endpoint requires authentication."""
    resp = client.get("/me")
    assert resp.status_code == 401


def test_me_with_invalid_token(client) -> None:
    """Test that /me endpoint rejects invalid tokens."""
    resp = client.get("/me", headers={"Authorization": "Bearer invalid-token"})
    assert resp.status_code == 401


def test_login_without_registration(client) -> None:
    """Test that login fails for unregistered users."""
    resp = client.post("/login", json={"username": "unregistered", "password": "secret"})
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_register_missing_fields(client) -> None:
    """Test that registration fails with missing required fields."""
    # Missing username
    resp = client.post("/register", json={"email": "test@example.com", "password": "secret"})
    assert resp.status_code == 422

    # Missing password
    resp = client.post("/register", json={"username": "test", "email": "test@example.com"})
    assert resp.status_code == 422


def test_token_expiry_behavior(client) -> None:
    """Test that tokens work for authenticated requests."""
    # Register and login
    resp = client.post("/register", json={"username": "tokentest", "email": "t@example.com", "password": "secret"})
    assert resp.status_code == 200

    token_resp = client.post("/login", json={"username": "tokentest", "password": "secret"})
    assert token_resp.status_code == 200

    token = token_resp.json()["token"]

    # Use token for authenticated request
    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "tokentest"


def test_password_security(client) -> None:
    """Test that passwords are properly secured."""
    # Register user
    resp = client.post("/register", json={"username": "security", "email": "sec@example.com", "password": "secret123"})
    assert resp.status_code == 200

    user_data = resp.json()

    # Password should not be in response
    assert "password" not in user_data
    assert "password_hash" not in user_data

    # Should be able to login with correct password
    login_resp = client.post("/login", json={"username": "security", "password": "secret123"})
    assert login_resp.status_code == 200

    # Should fail with wrong password
    wrong_resp = client.post("/login", json={"username": "security", "password": "wrongpassword"})
    assert wrong_resp.status_code == 401
