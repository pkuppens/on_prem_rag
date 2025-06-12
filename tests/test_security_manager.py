from datetime import timedelta

from backend.security.security_manager import SecurityManager


def test_create_and_verify_token() -> None:
    manager = SecurityManager("secret")
    token = manager.create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=1))
    data = manager.verify_token(token)
    assert data is not None
    assert data["sub"] == "user"
