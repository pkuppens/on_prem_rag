"""Query Service — Bounded Context for RAG query orchestration.

This bounded context owns the full RAG workflow: accept user question →
check access → sanitize PII → retrieve context → build prompt →
generate answer → audit log → return response.

It is the flagship BC that ties together all other BCs (LLM Gateway,
Retrieval, Access Control, Privacy Guard, Audit Trail) via anti-corruption
layer adapters.
"""

from backend.query_service.application.query_orchestrator import QueryOrchestrator
from backend.query_service.domain.aggregates import Conversation
from backend.query_service.domain.entities import Query, Answer, Citation
from backend.query_service.domain.interfaces import IQueryOrchestrator

__all__ = [
    "Conversation",
    "Query",
    "Answer",
    "Citation",
    "IQueryOrchestrator",
    "QueryOrchestrator",
]
