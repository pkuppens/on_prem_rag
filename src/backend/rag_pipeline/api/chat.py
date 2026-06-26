"""Compatibility shim — delegates to the Query Service API.

Re-exports all symbols from backend.query_service.api.chat for backward
compatibility during the Query Service BC migration.
"""

from backend.query_service.api.chat import (  # noqa: F401
    ChatMessage,
    ChatRequest,
    ChatResponse,
    _format_sse,
    _stream_chat_response,
    chat,
    chat_stream,
    router,
)

# Backward-compatible alias: old code referenced `qa_system`, new code uses `orchestrator`
from backend.query_service.api.chat import orchestrator as qa_system  # noqa: F401

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "chat",
    "chat_stream",
    "qa_system",
    "router",
]
