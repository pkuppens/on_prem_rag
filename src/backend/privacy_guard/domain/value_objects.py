"""Privacy Guard Value Objects.

Defines the PII taxonomy and cloud-safety classification model.

Cloud-Safety Criterion: TRACEABILITY
- Can this data point be used to identify a specific individual?
- Direct identifiers: NEVER cloud-safe (name, BSN, exact DoB)
- Quasi-identifiers: Cloud-safe AFTER transformation (age→decade)
- Non-PII: Cloud-safe as-is (symptoms, medication names)

Threat Model:
- Eavesdroppers on communication channel
- Cloud provider conversation history storage
- Both are mitigated by ensuring no traceable PII in transmitted queries

Reference: WBSO-AICM-2025-01 Knelpunt 2 (AVG-veilig)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Callable


class PIICategory(Enum):
    """Classification of personally identifiable information.

    Categories are organized by identifiability:
    - Direct identifiers: Uniquely identify a person on their own
    - Quasi-identifiers: May identify when combined with other data
    """

    # DIRECT IDENTIFIERS - uniquely identify a person
    NAME = "name"
    BSN = "bsn"
    DOB_EXACT = "dob_exact"
    ADDRESS = "address"
    PHONE = "phone"
    EMAIL = "email"
    PATIENT_ID = "patient_id"

    # QUASI-IDENTIFIERS - may identify when combined
    AGE_EXACT = "age_exact"
    POSTAL_CODE = "postal_code"
    DATE_SPECIFIC = "date_specific"

    @property
    def is_direct_identifier(self) -> bool:
        """Returns True if this is a direct identifier."""
        return self in (
            PIICategory.NAME,
            PIICategory.BSN,
            PIICategory.DOB_EXACT,
            PIICategory.ADDRESS,
            PIICategory.PHONE,
            PIICategory.EMAIL,
            PIICategory.PATIENT_ID,
        )

    @property
    def is_quasi_identifier(self) -> bool:
        """Returns True if this is a quasi-identifier."""
        return self in (
            PIICategory.AGE_EXACT,
            PIICategory.POSTAL_CODE,
            PIICategory.DATE_SPECIFIC,
        )

    @property
    def dutch_label(self) -> str:
        """Dutch label for this PII category (for audit logs)."""
        labels = {
            PIICategory.NAME: "Naam",
            PIICategory.BSN: "BSN",
            PIICategory.DOB_EXACT: "Geboortedatum",
            PIICategory.ADDRESS: "Adres",
            PIICategory.PHONE: "Telefoonnummer",
            PIICategory.EMAIL: "E-mailadres",
            PIICategory.PATIENT_ID: "Patiëntnummer",
            PIICategory.AGE_EXACT: "Leeftijd",
            PIICategory.POSTAL_CODE: "Postcode",
            PIICategory.DATE_SPECIFIC: "Specifieke datum",
        }
        return labels[self]


class CloudSafety(Enum):
    """Cloud transmission safety classification."""

    NEVER = "never"  # Must NEVER go to cloud (direct PII)
    AFTER_TRANSFORM = "transform"  # Safe after anonymization
    SAFE = "safe"  # Can go to cloud as-is


@dataclass(frozen=True)
class PIIType:
    """Definition of a PII type with detection and transformation rules.

    Each PII type defines:
    - How to detect it (regex pattern)
    - Whether it can ever go to cloud (cloud_safety)
    - How to transform it for cloud transmission (transform token)
    """

    category: PIICategory
    cloud_safety: CloudSafety
    description: str
    examples: tuple[str, ...]
    pattern: str | None  # Regex pattern for detection
    transform_token: str  # Replacement token for anonymization

    def matches(self, text: str) -> list[re.Match]:
        """Find all matches of this PII type in text."""
        if self.pattern is None:
            return []
        return list(re.finditer(self.pattern, text, re.IGNORECASE))


# PII Type Registry - defines all PII types and how to handle them
PII_TYPES: dict[PIICategory, PIIType] = {
    PIICategory.NAME: PIIType(
        category=PIICategory.NAME,
        cloud_safety=CloudSafety.NEVER,
        description="Personal names including first, last, maiden names",
        examples=("Jan de Vries", "mevr. Jansen", "dhr. Bakker"),
        # Pattern matches Dutch name prefixes and capitalized names
        pattern=(
            r"(?:dhr\.|mevr\.|de heer|mevrouw)\s+"
            r"[A-Z][a-zA-Zéèëïöüáàâäîôû]+"
            r"(?:\s+(?:van|de|den|der|het|'t)\s+)?"
            r"[A-Z]?[a-zA-Zéèëïöüáàâäîôû]*"
        ),
        transform_token="[PERSOON]",
    ),
    PIICategory.BSN: PIIType(
        category=PIICategory.BSN,
        cloud_safety=CloudSafety.NEVER,
        description="Dutch Burgerservicenummer (9 digits, 11-proof)",
        examples=("123456789", "BSN: 987654321"),
        # Basic 9-digit pattern; real implementation needs 11-proof validation
        pattern=r"\b\d{9}\b",
        transform_token="[BSN]",
    ),
    PIICategory.DOB_EXACT: PIIType(
        category=PIICategory.DOB_EXACT,
        cloud_safety=CloudSafety.NEVER,
        description="Exact date of birth",
        examples=("14 februari 1953", "1953-02-14", "14-02-1953"),
        # Matches common Dutch date formats
        pattern=(
            r"\b(?:"
            r"\d{1,2}[-/\s](?:januari|februari|maart|april|mei|juni|juli|augustus|"
            r"september|oktober|november|december)[-/\s]\d{4}"
            r"|\d{1,2}[-/]\d{1,2}[-/]\d{4}"
            r"|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"
        ),
        transform_token="[GEBOORTEDATUM]",
    ),
    PIICategory.ADDRESS: PIIType(
        category=PIICategory.ADDRESS,
        cloud_safety=CloudSafety.NEVER,
        description="Street address with house number",
        examples=("Hoofdstraat 123", "Kerkweg 45a", "Van Goghplein 7"),
        # Matches Dutch street name patterns
        pattern=r"[A-Z][a-zA-Z]+(?:straat|weg|laan|plein|gracht|singel|kade|dijk|pad|hof|steeg|dreef|park|markt)\s+\d+\s*[a-zA-Z]?",
        transform_token="[ADRES]",
    ),
    PIICategory.POSTAL_CODE: PIIType(
        category=PIICategory.POSTAL_CODE,
        cloud_safety=CloudSafety.AFTER_TRANSFORM,
        description="Dutch postal code (4 digits + 2 letters)",
        examples=("1234 AB", "5678CD"),
        pattern=r"\b\d{4}\s?[A-Z]{2}\b",
        transform_token="[REGIO]",  # Transform to first 2 digits only
    ),
    PIICategory.PHONE: PIIType(
        category=PIICategory.PHONE,
        cloud_safety=CloudSafety.NEVER,
        description="Dutch phone number",
        examples=("06-12345678", "+31 6 1234 5678", "020-1234567"),
        pattern=r"(?:\+31|0)\s*(?:6|[1-9]\d)\s*[-\s]?\d{2,4}\s*[-\s]?\d{2,4}\s*[-\s]?\d{0,4}",
        transform_token="[TELEFOON]",
    ),
    PIICategory.EMAIL: PIIType(
        category=PIICategory.EMAIL,
        cloud_safety=CloudSafety.NEVER,
        description="Email address",
        examples=("jan@example.nl", "patient@gmail.com"),
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        transform_token="[EMAIL]",
    ),
    PIICategory.AGE_EXACT: PIIType(
        category=PIICategory.AGE_EXACT,
        cloud_safety=CloudSafety.AFTER_TRANSFORM,
        description="Exact age - can be generalized to decade",
        examples=("72 jaar", "leeftijd: 45", "45-jarige"),
        pattern=r"\b(\d{1,3})\s*(?:jaar|jarige?)\b",
        transform_token="[LEEFTIJD]",  # Transform to decade: 72 → "70+"
    ),
    PIICategory.PATIENT_ID: PIIType(
        category=PIICategory.PATIENT_ID,
        cloud_safety=CloudSafety.NEVER,
        description="Patient or medical record number",
        examples=("patiëntnummer 12345", "MRN: A123456"),
        pattern=r"(?:pati[eë]nt(?:nummer|id|nr)|MRN|dossier(?:nummer|nr)?)[:\s]*[A-Za-z0-9-]+",
        transform_token="[PATIENTNR]",
    ),
    PIICategory.DATE_SPECIFIC: PIIType(
        category=PIICategory.DATE_SPECIFIC,
        cloud_safety=CloudSafety.AFTER_TRANSFORM,
        description="Specific dates that could identify events",
        examples=("op 14 maart 2024", "sinds 1 januari"),
        pattern=(
            r"\b(?:op|sinds|vanaf|tot)\s+\d{1,2}\s+"
            r"(?:januari|februari|maart|april|mei|juni|juli|augustus|"
            r"september|oktober|november|december)(?:\s+\d{4})?\b"
        ),
        transform_token="[DATUM]",  # Transform to relative or season
    ),
}


def get_pii_type(category: PIICategory) -> PIIType:
    """Get the PII type definition for a category."""
    return PII_TYPES[category]


@dataclass(frozen=True)
class PIIDetection:
    """Result of detecting PII in text.

    Captures the detected PII instance with its location and type
    for subsequent transformation.
    """

    category: PIICategory
    original_value: str
    start_position: int
    end_position: int
    confidence: float = 1.0  # 0.0 to 1.0 (pattern match = 1.0, LLM = varies)

    @property
    def cloud_safety(self) -> CloudSafety:
        """Get the cloud safety classification for this PII type."""
        return PII_TYPES[self.category].cloud_safety

    @property
    def transform_token(self) -> str:
        """Get the replacement token for this PII type."""
        return PII_TYPES[self.category].transform_token

    @property
    def is_direct_identifier(self) -> bool:
        """Returns True if this is a direct identifier."""
        return self.category.is_direct_identifier

    def to_audit_record(self) -> dict:
        """Convert to audit-safe record (no actual PII values)."""
        return {
            "category": self.category.value,
            "category_label": self.category.dutch_label,
            "position": f"{self.start_position}-{self.end_position}",
            "confidence": self.confidence,
            "cloud_safety": self.cloud_safety.value,
        }


@dataclass(frozen=True)
class Transformation:
    """Record of a PII transformation applied to text.

    Captures what was transformed and how, for audit purposes.
    The original value is NOT stored in audit logs - only the fact
    that a transformation occurred.
    """

    category: PIICategory
    action: str  # "removed", "replaced", "generalized"
    token_used: str  # The replacement token
    position_start: int
    position_end: int

    def to_audit_record(self) -> dict:
        """Convert to audit record."""
        return {
            "category": self.category.value,
            "action": self.action,
            "token": self.token_used,
        }


@dataclass(frozen=True)
class AnonymizedText:
    """Text with PII replaced by tokens, plus metadata for audit.

    This is the output of the anonymization pipeline. The original text
    is NOT stored - only a hash for correlation. The anonymized text
    IS stored because it's what gets sent to the cloud (and must be
    inspectable by auditors).
    """

    original_hash: str  # SHA-256 of original (for audit correlation)
    anonymized_text: str  # Text with PII replaced (this IS stored)
    pii_detected: tuple[PIIDetection, ...]
    transformations: tuple[Transformation, ...]
    is_cloud_safe: bool  # True if all PII has been handled

    @property
    def pii_count(self) -> int:
        """Number of PII instances detected."""
        return len(self.pii_detected)

    @property
    def pii_categories_found(self) -> set[PIICategory]:
        """Set of PII categories that were detected."""
        return {d.category for d in self.pii_detected}

    @property
    def had_direct_identifiers(self) -> bool:
        """Returns True if direct identifiers were found (and removed)."""
        return any(d.is_direct_identifier for d in self.pii_detected)

    def to_audit_entry(self) -> dict:
        """Convert to audit log entry format.

        This is what the auditor sees - the anonymized text plus
        metadata about what was transformed.
        """
        return {
            "original_hash": self.original_hash,
            "anonymized_text": self.anonymized_text,  # Auditor CAN see this
            "pii_summary": {
                "total_detected": self.pii_count,
                "categories": [c.value for c in self.pii_categories_found],
                "had_direct_identifiers": self.had_direct_identifiers,
            },
            "transformations": [t.to_audit_record() for t in self.transformations],
            "cloud_safe": self.is_cloud_safe,
        }


@dataclass(frozen=True)
class CloudEligibility:
    """Result of cloud eligibility check.

    Determines whether a query can be sent to a cloud LLM based on
    the PII analysis and transformation results.
    """

    eligible: bool
    reason: str
    anonymized_text: AnonymizedText | None = None
    fallback_to_local: bool = False

    @classmethod
    def approved(cls, anonymized: AnonymizedText) -> CloudEligibility:
        """Create an APPROVED eligibility decision."""
        return cls(
            eligible=True,
            reason="Query anonymized successfully - safe for cloud transmission",
            anonymized_text=anonymized,
        )

    @classmethod
    def denied_pii_remains(cls, categories: set[PIICategory]) -> CloudEligibility:
        """Create a DENIED decision due to remaining PII."""
        cat_names = ", ".join(c.dutch_label for c in categories)
        return cls(
            eligible=False,
            reason=f"PII could not be removed: {cat_names}",
            fallback_to_local=True,
        )

    @classmethod
    def denied_policy(cls, policy_reason: str) -> CloudEligibility:
        """Create a DENIED decision due to policy."""
        return cls(
            eligible=False,
            reason=f"Policy restriction: {policy_reason}",
            fallback_to_local=True,
        )


def hash_text(text: str) -> str:
    """Create SHA-256 hash of text for audit correlation."""
    return sha256(text.encode("utf-8")).hexdigest()


def age_to_decade(age: int) -> str:
    """Transform exact age to decade range.

    Examples:
        72 → "70+"
        45 → "40s"
        38 → "late 30s"
    """
    decade = (age // 10) * 10
    if age >= 70:
        return f"{decade}+"
    return f"{decade}s"


def postal_code_to_region(postal_code: str) -> str:
    """Transform full postal code to region level.

    Example: "1234 AB" → "12xx" (first 2 digits only)
    """
    # Extract first 2 digits
    digits = "".join(c for c in postal_code if c.isdigit())
    if len(digits) >= 2:
        return f"{digits[:2]}xx regio"
    return "[REGIO]"


# Transformation examples for documentation
TRANSFORMATION_EXAMPLES = """
┌────────────────────────────────────────────────────────────────────┐
│ TRANSFORMATION EXAMPLES                                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ORIGINAL (NOT cloud-safe):                                        │
│ "Dhr. de Vries, geboren 14 februari 1953, BSN 123456789,          │
│  wonend Hoofdstraat 45, 1234 AB Amsterdam, 72 jaar oud"           │
│                                                                    │
│ ANONYMIZED (cloud-safe):                                          │
│ "[PERSOON], geboren [GEBOORTEDATUM], BSN [BSN],                   │
│  wonend [ADRES], 12xx regio Amsterdam, 70+ jaar oud"              │
│                                                                    │
│ RESTRUCTURED CLOUD QUERY (what actually gets sent):               │
│ "Mannelijke patiënt, 70+, met klachten van pijn op de borst       │
│  en kortademigheid. Voorgeschiedenis van hypertensie.             │
│  Wat zijn de differentiaaldiagnoses en aanbevolen vervolgstappen?"│
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
"""
