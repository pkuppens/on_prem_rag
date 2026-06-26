"""Compatibility shim — delegates to the Query Service API.

Re-exports all symbols from backend.query_service.api.query for backward
compatibility during the Query Service BC migration.
"""

from backend.query_service.api.query import (  # noqa: F401
    ConversationRequest,
    QueryRequest,
    process_conversation_endpoint,
    query_documents,
    query_service,
    router,
)

__all__ = [
    "ConversationRequest",
    "QueryRequest",
    "process_conversation_endpoint",
    "query_documents",
    "query_service",
    "router",
]
