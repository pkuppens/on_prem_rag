import time
from datetime import timedelta

from backend.security.security_manager import SecurityManager


def test_create_and_verify_token() -> None:
    """As a service, I want valid tokens to decode correctly so authenticated calls succeed."""
    manager = SecurityManager("secret")
    token = manager.create_access_token({"sub": "user"}, expires_delta=timedelta(minutes=5))
    data = manager.verify_token(token)
    assert data is not None
    assert data["sub"] == "user"


def test_verify_token_rejects_expired() -> None:
    """As a security control, I want expired tokens to be rejected so stolen tokens cannot be replayed."""
    manager = SecurityManager("secret")
    # Create a token with a negative delta so exp is already in the past
    token = manager.create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-1))
    result = manager.verify_token(token)
    assert result is None, "Expired token must not verify — replay attack window must be bounded"


def test_verify_token_rejects_tampered_signature() -> None:
    """As a security control, I want tampered tokens to be rejected so JWT forgery is prevented."""
    manager = SecurityManager("correct-secret")
    token = manager.create_access_token({"sub": "admin"})
    # Attempt to verify with a different secret
    attacker = SecurityManager("wrong-secret")
    result = attacker.verify_token(token)
    assert result is None, "Token signed with a different secret must not verify"


def test_verify_token_rejects_wrong_algorithm() -> None:
    """As a security control, I want tokens using unexpected algorithms to be rejected."""
    manager_hs256 = SecurityManager("shared-secret", algorithm="HS256")
    manager_hs512 = SecurityManager("shared-secret", algorithm="HS512")
    token = manager_hs256.create_access_token({"sub": "user"})
    # HS512 manager must not accept an HS256 token
    result = manager_hs512.verify_token(token)
    assert result is None, "Token with unexpected algorithm must not verify"
