"""AuditService — coordinates audit entry creation and storage.

This is the primary application service for the Audit Trail BC.
It depends on IAuditStore (Dependency Inversion) and delegates
entry creation to the domain entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from backend.audit_trail.application.wbso_report_generator import WBSOReport, WBSOReportGenerator
from backend.audit_trail.domain.entities import (
    CloudQueryAuditEntry,
    GuardrailAction,
    GuardrailEventEntry,
    GuardrailType,
    PatientIsolationAuditEntry,
)
from backend.audit_trail.domain.value_objects import (
    ActorReference,
    AuditMetadata,
    ResourceReference,
)
from backend.audit_trail.ports.audit_store import AuditEntry, AuditQuery, IAuditStore


class AuditService:
    """Application service for audit trail operations.

    Creates typed audit entries and delegates persistence to the
    injected IAuditStore implementation.
    """

    def __init__(self, store: IAuditStore) -> None:
        self._store = store

    def log_cloud_query(
        self,
        actor: ActorReference,
        resource: ResourceReference,
        metadata: AuditMetadata,
        *,
        cloud_query_text: str = "",
        cloud_provider: str = "",
        response_received: bool = False,
        latency_ms: int = 0,
        pii_categories_detected: List[str] | None = None,
        pii_count: int = 0,
        transformations_applied: List[str] | None = None,
    ) -> CloudQueryAuditEntry:
        """Create and store a CloudQueryAuditEntry."""
        entry = CloudQueryAuditEntry(
            cloud_query_text=cloud_query_text,
            original_query_hash=metadata.query_hash,
            pii_categories_detected=pii_categories_detected or [],
            pii_count=pii_count,
            transformations_applied=transformations_applied or [],
            user_role=actor.role,
            session_hash=actor.session_hash,
            cloud_provider=cloud_provider,
            response_received=response_received,
            latency_ms=latency_ms,
        )
        self._store.store(entry)
        return entry

    def log_guardrail_event(
        self,
        actor: ActorReference,
        guardrail_type: GuardrailType,
        action: GuardrailAction,
        metadata: AuditMetadata,
        *,
        reason_code: str = "",
        processing_time_ms: int = 0,
        confidence_score: float = 1.0,
    ) -> GuardrailEventEntry:
        """Create and store a GuardrailEventEntry."""
        entry = GuardrailEventEntry(
            guardrail_type=guardrail_type,
            action_taken=action,
            reason_code=reason_code,
            query_hash=metadata.query_hash,
            user_role=actor.role,
            processing_time_ms=processing_time_ms,
            confidence_score=confidence_score,
        )
        self._store.store(entry)
        return entry

    def log_isolation_check(
        self,
        actor: ActorReference,
        patient_id: str,
        metadata: AuditMetadata,
        *,
        requested_scope_hashes: List[str] | None = None,
        response_scope_hashes: List[str] | None = None,
        isolation_maintained: bool = True,
        blocked_count: int = 0,
    ) -> PatientIsolationAuditEntry:
        """Create and store a PatientIsolationAuditEntry."""
        from backend.audit_trail.domain.value_objects import hash_identifier

        entry = PatientIsolationAuditEntry(
            requesting_patient_hash=hash_identifier(patient_id),
            requested_scope_hashes=requested_scope_hashes or [],
            response_scope_hashes=response_scope_hashes or [],
            isolation_maintained=isolation_maintained,
            mismatch_detected=not isolation_maintained,
            blocked_count=blocked_count,
        )
        self._store.store(entry)
        return entry

    def query_entries(self, filters: AuditQuery | None = None) -> List[AuditEntry]:
        """Query stored audit entries with optional filters."""
        return self._store.query(filters or AuditQuery())

    def generate_wbso_report(self, start_date: datetime, end_date: datetime) -> WBSOReport:
        """Generate a WBSO evidence report for the given date range."""
        filters = AuditQuery(start_date=start_date, end_date=end_date)
        entries = self._store.query(filters)
        generator = WBSOReportGenerator(entries, start_date=start_date, end_date=end_date)
        return generator.generate()
