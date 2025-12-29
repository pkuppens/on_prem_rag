"""Privacy Guard Bounded Context.

Implements WBSO Knelpunt 2: Cloud LLM zonder privacylek (GDPR-safe Cloud).

This context handles PII detection, anonymization, and cloud routing decisions:
- PII taxonomy and classification
- Anonymization/pseudonymization transforms
- Cloud eligibility checking
- De-anonymization for responses

Reference: WBSO-AICM-2025-01 WP2 (07-2025)
"""

from backend.privacy_guard.domain.value_objects import (
    PII_TYPES,
    AnonymizedText,
    CloudSafety,
    PIICategory,
    PIIDetection,
    PIIType,
)

__all__ = [
    "AnonymizedText",
    "CloudSafety",
    "PIICategory",
    "PIIDetection",
    "PIIType",
    "PII_TYPES",
]
