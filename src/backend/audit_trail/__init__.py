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

__all__ = [
    "ActorReference",
    "AuditMetadata",
    "CloudQueryAuditEntry",
    "GuardrailAction",
    "GuardrailEventEntry",
    "GuardrailType",
    "PatientIsolationAuditEntry",
    "ResourceReference",
]
