"""Adapter to the Audit Trail BC.

Connects the Query Service's IAuditTrail port to the Audit Trail BC's
AuditService.
"""

from __future__ import annotations

from typing import Any

from backend.audit_trail.application.audit_service import AuditService
from backend.audit_trail.domain.value_objects import (
    ActorReference,
    AuditMetadata,
    ResourceReference,
)

from backend.query_service.ports.audit import IAuditTrail


class AuditTrailAdapter(IAuditTrail):
    """Adapter that delegates to the Audit Trail BC.

    Wraps the AuditService and translates Query Service events into
    Audit Trail domain types.
    """

    def __init__(self, audit_service: AuditService | None = None) -> None:
        """Initialize with an optional AuditService.

        Args:
            audit_service: The AuditService to delegate to.
                If None, creates a no-op adapter that logs nothing.
        """
        self._service = audit_service

    def log_query_received(self, query_id: str, question: str, user_id: str, session_id: str) -> None:
        """Log query received via the AuditService."""
        if not self._service:
            return

        import hashlib

        actor = ActorReference(
            user_id=user_id,
            session_hash=hashlib.sha256(session_id.encode()).hexdigest()[:16] if session_id else "",
        )
        resource = ResourceReference(
            resource_type="query",
            resource_id=query_id,
        )
        metadata = AuditMetadata(
            query_hash=hashlib.sha256(question.encode()).hexdigest()[:32],
        )

        self._service.log_cloud_query(
            actor=actor,
            resource=resource,
            metadata=metadata,
            cloud_query_text=question[:200],
            cloud_provider="local",
        )

    def log_retrieval(self, query_id: str, chunk_count: int, strategy: str) -> None:
        """Log retrieval event."""
        # No dedicated retrieval log method in AuditService yet
        # Logged as part of the query context
        pass

    def log_answer(self, query_id: str, question: str, answer: str, confidence: str) -> None:
        """Log answer generation."""
        # Currently handled as part of the cloud query event above
        pass

    def log_error(self, query_id: str, error: str, stage: str) -> None:
        """Log an error during query processing."""
        if not self._service:
            return

        from backend.audit_trail.domain.entities import GuardrailAction, GuardrailType

        import hashlib

        actor = ActorReference(
            user_id="system",
            session_hash="",
        )
        metadata = AuditMetadata(
            query_hash=hashlib.sha256(query_id.encode()).hexdigest()[:32],
        )

        self._service.log_guardrail_event(
            actor=actor,
            guardrail_type=GuardrailType.INPUT_VALIDATION,
            action=GuardrailAction.BLOCKED,
            metadata=metadata,
            reason_code=f"QUERY_ERROR:{stage}:{error[:100]}",
        )
