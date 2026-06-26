"""Audit Trail Bounded Context.

Implements WBSO Knelpunt 3: Privacyvriendelijke auditlogging (Privacy-safe Auditing).

This context provides guardrail monitoring - proving the security system works:
- Cloud Query Log: Stores anonymized queries for inspection
- Guardrail Event Log: Records security decisions
- Patient Isolation Log: Verifies data isolation

Primary WBSO Claim: Queries to cloud do NOT contain PII.
The audit system provides the evidence for this claim.

Reference: WBSO-AICM-2025-01 WP3 (08-2025)
"""

from backend.audit_trail.application.audit_service import AuditService
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
from backend.audit_trail.infrastructure.audit_store import FileAuditStore, InMemoryAuditStore
from backend.audit_trail.ports.audit_store import AuditQuery, IAuditStore

__all__ = [
    "ActorReference",
    "AuditMetadata",
    "AuditQuery",
    "AuditService",
    "CloudQueryAuditEntry",
    "FileAuditStore",
    "GuardrailAction",
    "GuardrailEventEntry",
    "GuardrailType",
    "IAuditStore",
    "InMemoryAuditStore",
    "PatientIsolationAuditEntry",
    "ResourceReference",
    "WBSOReport",
    "WBSOReportGenerator",
]
