"""Audit Trail Value Objects.

Defines privacy-preserving references for audit logging.

Design Principle: Audit logs must be useful for compliance verification
WITHOUT storing personally identifiable information.

- Actor references use hashed user IDs (auditor can verify but not identify)
- Resource references use hashed patient IDs
- Query content is stored ONLY for anonymized cloud queries (to prove no PII)
- Original query content is NEVER stored (only hash for correlation)

Reference: WBSO-AICM-2025-01 Knelpunt 3 (Privacyvriendelijke auditlogs)
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import List


def hash_identifier(identifier: str, salt: str = "") -> str:
    """Create a one-way hash of an identifier.

    The hash allows correlation across audit entries without exposing
    the actual identifier. With the same salt, the same identifier
    always produces the same hash.

    Args:
        identifier: The value to hash (user_id, patient_id, etc.)
        salt: Optional salt for additional security

    Returns:
        Hex-encoded SHA-256 hash (first 16 characters for readability)
    """
    combined = f"{salt}:{identifier}" if salt else identifier
    full_hash = sha256(combined.encode("utf-8")).hexdigest()
    return full_hash[:16]  # Shortened for readability in logs


@dataclass(frozen=True)
class ActorReference:
    """Privacy-safe reference to a user/actor.

    The auditor can see WHAT role performed an action, but cannot
    directly identify WHO the person is. The hash allows correlation
    across multiple audit entries for the same user.
    """

    actor_hash: str  # Hashed user ID
    role: str  # Role at time of action (gp, patient, admin, auditor)
    session_hash: str  # Hashed session ID for grouping related actions

    @classmethod
    def from_user(cls, user_id: str, role: str, session_id: str) -> ActorReference:
        """Create an actor reference from user details."""
        return cls(
            actor_hash=hash_identifier(user_id),
            role=role,
            session_hash=hash_identifier(session_id),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "actor_hash": self.actor_hash,
            "role": self.role,
            "session_hash": self.session_hash,
        }


@dataclass(frozen=True)
class ResourceReference:
    """Privacy-safe reference to a resource (e.g., patient record).

    Allows auditing of which resources were accessed without exposing
    the actual patient identifiers.
    """

    resource_hash: str  # Hashed resource ID (e.g., patient ID)
    resource_type: str  # Type of resource (patient_record, document, etc.)
    collection: str  # Which collection/table was accessed
    scope_hash: str  # Hashed query scope (for multi-patient queries)

    @classmethod
    def from_patient(cls, patient_id: str, collection: str = "patient_records") -> ResourceReference:
        """Create a resource reference for a patient record."""
        return cls(
            resource_hash=hash_identifier(patient_id),
            resource_type="patient_record",
            collection=collection,
            scope_hash=hash_identifier(patient_id),
        )

    @classmethod
    def from_query_scope(cls, patient_ids: List[str], collection: str = "patient_records") -> ResourceReference:
        """Create a resource reference for a multi-patient query scope."""
        # Create a combined hash of all patient IDs in scope
        combined = ":".join(sorted(patient_ids))
        return cls(
            resource_hash=hash_identifier(combined),
            resource_type="query_scope",
            collection=collection,
            scope_hash=hash_identifier(combined),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "resource_hash": self.resource_hash,
            "resource_type": self.resource_type,
            "collection": self.collection,
            "scope_hash": self.scope_hash,
        }


@dataclass(frozen=True)
class AuditMetadata:
    """Non-sensitive operational metadata for audit entries.

    This metadata provides context for audit entries without
    containing any PII. It's useful for:
    - Performance monitoring (latency)
    - Security monitoring (PII detection rates)
    - Compliance reporting (cloud routing decisions)
    """

    query_hash: str  # Hash of original query (for correlation)
    intent_category: str  # Classified intent (read, write, etc.)
    pii_detected: bool  # Whether PII was found
    pii_categories: List[str]  # Which PII types were found
    cloud_routed: bool  # Whether query went to cloud
    latency_ms: int  # Processing time
    confidence_score: float  # Confidence of any ML/LLM decisions

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "query_hash": self.query_hash,
            "intent_category": self.intent_category,
            "pii_detected": self.pii_detected,
            "pii_categories": self.pii_categories,
            "cloud_routed": self.cloud_routed,
            "latency_ms": self.latency_ms,
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def create(
        cls,
        original_query: str,
        intent: str,
        pii_categories: List[str],
        cloud_routed: bool,
        latency_ms: int,
        confidence: float = 1.0,
    ) -> AuditMetadata:
        """Create audit metadata from processing results."""
        return cls(
            query_hash=hash_identifier(original_query),
            intent_category=intent,
            pii_detected=len(pii_categories) > 0,
            pii_categories=pii_categories,
            cloud_routed=cloud_routed,
            latency_ms=latency_ms,
            confidence_score=confidence,
        )
