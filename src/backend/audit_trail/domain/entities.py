"""Audit Trail Entities.

Defines the three audit log types for guardrail monitoring:

1. CloudQueryAuditEntry: PRIMARY WBSO EVIDENCE
   - Stores the actual anonymized query sent to cloud
   - Auditor can inspect and verify no PII is present

2. GuardrailEventEntry: System behavior evidence
   - Records every security decision (allow/block/transform)
   - Proves guardrails are active and effective

3. PatientIsolationAuditEntry: Data isolation evidence
   - Verifies patient queries don't leak other patients' data
   - Compares requested scope vs returned scope

Reference: WBSO-AICM-2025-01 Knelpunt 3 (Privacyvriendelijke auditlogs)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from backend.audit_trail.domain.value_objects import hash_identifier


class GuardrailType(Enum):
    """Types of guardrails that can trigger audit events."""

    ACCESS_CONTROL = "access"  # Role/permission checks
    PII_SCREENING = "pii"  # PII detection and transformation
    DATA_INTEGRITY = "integrity"  # Mutation detection and blocking
    PATIENT_ISOLATION = "isolation"  # Cross-patient leak prevention
    JAILBREAK_DETECTION = "jailbreak"  # Prompt injection detection


class GuardrailAction(Enum):
    """Actions taken by guardrails."""

    ALLOWED = "allowed"  # Request passed guardrail
    BLOCKED = "blocked"  # Request denied by guardrail
    TRANSFORMED = "transformed"  # Request modified (e.g., PII removed)
    ESCALATED = "escalated"  # Sent for manual review
    WARNING = "warning"  # Passed but flagged for review


@dataclass
class CloudQueryAuditEntry:
    """AUDIT LOG 1: Records every query sent to cloud LLM.

    This is the PRIMARY WBSO evidence that PII does not reach the cloud.
    The actual anonymized query text IS stored (not hashed) so auditors
    can inspect and verify no PII is present.

    What's stored:
    - cloud_query_text: The exact text sent to cloud (MUST be PII-free)
    - original_query_hash: Hash of original for correlation (not the text!)
    - pii_categories_detected: Which PII types were found and handled
    - transformations_applied: What anonymization was done

    What's NOT stored:
    - The original query text (contains PII)
    - User identity (only role and session hash)
    - Patient identifiers (only hashes)
    """

    # Identity
    entry_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # THE KEY EVIDENCE: actual query sent to cloud (auditor can read this)
    cloud_query_text: str = ""

    # Correlation without exposing original content
    original_query_hash: str = ""

    # Evidence of PII handling
    pii_categories_detected: List[str] = field(default_factory=list)
    pii_count: int = 0
    transformations_applied: List[str] = field(default_factory=list)

    # Context without identifying the user
    user_role: str = ""  # "gp", "patient" (NOT user_id)
    session_hash: str = ""  # Hashed session ID for correlation

    # Cloud interaction metadata
    cloud_provider: str = ""
    response_received: bool = False
    latency_ms: int = 0

    def to_inspection_record(self) -> dict:
        """Format for auditor inspection - this IS the evidence.

        The auditor reads cloud_query_text to verify:
        1. No personal names
        2. No BSN numbers
        3. No exact dates of birth
        4. No addresses
        5. No other identifying information

        If any PII is found, the guardrail has FAILED.
        """
        return {
            "entry_id": str(self.entry_id),
            "timestamp": self.timestamp.isoformat(),
            "cloud_query": self.cloud_query_text,  # <-- The auditor reads this
            "pii_handling": {
                "categories_detected": self.pii_categories_detected,
                "count": self.pii_count,
                "transformations": self.transformations_applied,
            },
            "context": {
                "role": self.user_role,
                "provider": self.cloud_provider,
                "latency_ms": self.latency_ms,
            },
            "correlation": {
                "original_hash": self.original_query_hash,
                "session_hash": self.session_hash,
            },
        }


@dataclass
class GuardrailEventEntry:
    """AUDIT LOG 2: Records guardrail activations.

    Evidence that the security system is active and making decisions.
    Used for:
    - Verifying guardrails are not bypassed
    - Measuring guardrail effectiveness
    - Debugging false positives/negatives

    Does NOT contain:
    - Query content (only hash)
    - User identity (only role)
    - Patient data (only event metadata)
    """

    # Identity
    entry_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # What guardrail and what it did
    guardrail_type: GuardrailType = GuardrailType.ACCESS_CONTROL
    action_taken: GuardrailAction = GuardrailAction.ALLOWED
    reason_code: str = ""  # Machine-readable reason (not content)

    # Correlation
    query_hash: str = ""  # Hash of the triggering query
    user_role: str = ""  # Role, not identity

    # For WBSO metrics
    processing_time_ms: int = 0
    confidence_score: float = 1.0  # How confident was the detection (0-1)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "entry_id": str(self.entry_id),
            "timestamp": self.timestamp.isoformat(),
            "guardrail_type": self.guardrail_type.value,
            "action": self.action_taken.value,
            "reason_code": self.reason_code,
            "query_hash": self.query_hash,
            "user_role": self.user_role,
            "processing_time_ms": self.processing_time_ms,
            "confidence_score": self.confidence_score,
        }


@dataclass
class PatientIsolationAuditEntry:
    """AUDIT LOG 3: Records patient data isolation checks.

    Evidence that Patient role users cannot see other patients' data.

    For each patient query, we record:
    - requesting_patient_hash: Hash of patient making request
    - requested_scope_hashes: Hashes of patient IDs in query filter
    - response_scope_hashes: Hashes of patient IDs in response

    If response_scope contains hashes NOT in requested_scope,
    the isolation has FAILED.
    """

    # Identity
    entry_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Scope comparison (all hashed)
    requesting_patient_hash: str = ""  # Hash of patient making request
    requested_scope_hashes: List[str] = field(default_factory=list)
    response_scope_hashes: List[str] = field(default_factory=list)

    # The critical check
    isolation_maintained: bool = True  # True if no leakage detected
    mismatch_detected: bool = False  # True if response contained other patients

    # If mismatch, what was blocked
    blocked_count: int = 0  # How many records were filtered out

    def check_isolation(self) -> bool:
        """Verify that response scope is subset of requested scope.

        Returns True if isolation is maintained (no leakage).
        """
        requested_set = set(self.requested_scope_hashes)
        response_set = set(self.response_scope_hashes)

        # Response should only contain patients from the request scope
        leakage = response_set - requested_set
        self.isolation_maintained = len(leakage) == 0
        self.mismatch_detected = not self.isolation_maintained

        return self.isolation_maintained

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "entry_id": str(self.entry_id),
            "timestamp": self.timestamp.isoformat(),
            "requesting_patient_hash": self.requesting_patient_hash,
            "requested_scope_count": len(self.requested_scope_hashes),
            "response_scope_count": len(self.response_scope_hashes),
            "isolation_maintained": self.isolation_maintained,
            "mismatch_detected": self.mismatch_detected,
            "blocked_count": self.blocked_count,
        }


@dataclass
class GuardrailEffectivenessReport:
    """Summary statistics proving guardrails work.

    This is what you show in WBSO documentation as evidence that
    the technical uncertainties have been resolved.
    """

    report_period_start: datetime = field(default_factory=datetime.utcnow)
    report_period_end: datetime = field(default_factory=datetime.utcnow)

    # Cloud PII Protection statistics
    total_cloud_queries: int = 0
    queries_with_pii_detected: int = 0
    queries_with_pii_transformed: int = 0
    pii_categories_blocked: dict = field(default_factory=dict)

    # Guardrail Activity statistics
    total_guardrail_events: int = 0
    events_by_type: dict = field(default_factory=dict)
    events_by_action: dict = field(default_factory=dict)

    # Patient Isolation statistics
    total_patient_queries: int = 0
    isolation_checks_passed: int = 0
    isolation_breaches_prevented: int = 0

    @property
    def cloud_pii_protection_rate(self) -> float:
        """Percentage of queries where PII was successfully handled.

        Target: 100% (all detected PII should be transformed).
        """
        if self.queries_with_pii_detected == 0:
            return 1.0
        return self.queries_with_pii_transformed / self.queries_with_pii_detected

    @property
    def isolation_success_rate(self) -> float:
        """Percentage of patient queries with proper isolation.

        Target: 100% (no cross-patient leakage).
        """
        if self.total_patient_queries == 0:
            return 1.0
        return self.isolation_checks_passed / self.total_patient_queries

    @property
    def guardrail_block_rate(self) -> float:
        """Percentage of requests blocked by guardrails.

        This is NOT a target - it shows guardrails are active.
        """
        if self.total_guardrail_events == 0:
            return 0.0
        blocked = self.events_by_action.get("blocked", 0)
        return blocked / self.total_guardrail_events

    def to_wbso_evidence(self) -> dict:
        """Format for WBSO documentation.

        This summary demonstrates:
        1. The system actively detects and handles PII
        2. No PII reaches cloud LLM queries
        3. Patient data isolation is enforced
        """
        return {
            "report_period": {
                "start": self.report_period_start.isoformat(),
                "end": self.report_period_end.isoformat(),
            },
            "cloud_pii_protection": {
                "total_queries": self.total_cloud_queries,
                "pii_detected_count": self.queries_with_pii_detected,
                "pii_transformed_count": self.queries_with_pii_transformed,
                "protection_rate": f"{self.cloud_pii_protection_rate:.1%}",
                "pii_categories": self.pii_categories_blocked,
            },
            "guardrail_activity": {
                "total_events": self.total_guardrail_events,
                "by_type": self.events_by_type,
                "by_action": self.events_by_action,
                "block_rate": f"{self.guardrail_block_rate:.1%}",
            },
            "patient_isolation": {
                "total_patient_queries": self.total_patient_queries,
                "isolation_maintained": self.isolation_checks_passed,
                "breaches_prevented": self.isolation_breaches_prevented,
                "success_rate": f"{self.isolation_success_rate:.1%}",
            },
            "wbso_claim_evidence": {
                "claim": "Queries to cloud do NOT contain PII",
                "evidence": "Cloud Query Audit Log with inspectable anonymized queries",
                "result": "PASS" if self.cloud_pii_protection_rate == 1.0 else "NEEDS_REVIEW",
            },
        }
