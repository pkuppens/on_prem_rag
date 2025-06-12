"""JWT-based security helper classes.

Implements token handling for [FEAT-006](../../../project/program/features/FEAT-006.md).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext


class SecurityManager:
    """Manage token creation and verification."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Return a signed JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Decode and validate a token. Returns claims or None."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except Exception:  # pragma: no cover - simple failure handling
            return None

    # TODO: add refresh token support and token revocation


__all__ = ["SecurityManager"]
