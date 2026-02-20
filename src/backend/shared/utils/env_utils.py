"""Environment variable wrapper utilities.

Centralizes env var access so defaults live in one place and model names
and other config can be updated via .env without code changes.
"""

from __future__ import annotations

import os


def get_env(key: str, default: str = "") -> str:
    """Get environment variable, stripped. Returns default if unset or empty.

    Args:
        key: Environment variable name.
        default: Value when key is unset or empty.

    Returns:
        Stripped value or default.
    """
    value = os.getenv(key, default)
    return (value or "").strip() or default


def get_env_or_none(key: str) -> str | None:
    """Get environment variable, stripped. Returns None if unset or empty.

    Args:
        key: Environment variable name.

    Returns:
        Stripped value or None.
    """
    value = (os.getenv(key) or "").strip()
    return value if value else None
