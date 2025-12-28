"""Audit Trail Domain Layer.

Contains the core domain model for guardrail monitoring and audit logging.
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
