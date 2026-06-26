"""Compatibility shim — re-exports public symbols from the Query Service API.

During the BC migration, this package delegates all public symbols
to backend.query_service.api for backward compatibility.
"""

from backend.query_service.api.app import app
from backend.query_service.api.ask import router as ask_router
from backend.query_service.api.chat import router as chat_router
from backend.query_service.api.documents import router as documents_router
from backend.query_service.api.health import router as health_router
from backend.query_service.api.metrics import router as metrics_router
from backend.query_service.api.parameters import router as parameters_router
from backend.query_service.api.query import router as query_router
from backend.query_service.api.websocket import router as websocket_router

__all__ = [
    "app",
    "ask_router",
    "chat_router",
    "documents_router",
    "health_router",
    "metrics_router",
    "parameters_router",
    "query_router",
    "websocket_router",
]
