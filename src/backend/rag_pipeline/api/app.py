"""Compatibility shim — delegates to the Query Service API.

Re-exports app from backend.query_service.api.app and start_server
from backend.query_service.main for backward compatibility.
"""

from backend.query_service.api.app import app  # noqa: F401
from backend.query_service.main import start_server  # noqa: F401

__all__ = [
    "app",
    "start_server",
]
