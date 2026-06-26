"""Anti-Corrosion Layer adapter to the Privacy Guard BC.

Translates Query Service sanitization requests into Privacy Guard
BC types (AnonymizedText, PIIDetection) and converts results back.
"""

from __future__ import annotations

from typing import Any

from backend.privacy_guard.domain.value_objects import AnonymizedText, CloudSafety, PIICategory, PIIType, hash_text

from backend.query_service.ports.privacy import IPrivacySanitizer

# Re-export for convenience
__all__ = ["PrivacyGuardAdapter"]


class PrivacyGuardAdapter(IPrivacySanitizer):
    """Adapter that delegates to the Privacy Guard BC.

    Uses the Privacy Guard domain value objects and PII taxonomy
    to detect and anonymize PII in user queries.
    """

    def sanitize(self, text: str, scope: str | None = None) -> tuple[str, dict[str, Any]]:
        """Sanitize text by detecting and removing PII.

        Applies replacement patterns for all registered PII types.

        Args:
            text: The text to sanitize.
            scope: Optional scope context (unused in basic implementation).

        Returns:
            Tuple of (sanitized_text, metadata).
        """
        from backend.privacy_guard.domain.value_objects import PII_TYPES

        sanitized = text
        detections: list[dict[str, Any]] = []

        for pii_type in PII_TYPES.values():
            matches = pii_type.matches(sanitized)
            for match in reversed(matches):  # Reverse to preserve positions
                sanitized = sanitized[: match.start()] + pii_type.transform_token + sanitized[match.end() :]
                detections.append({
                    "category": pii_type.category.value,
                    "token": pii_type.transform_token,
                    "position": {"start": match.start(), "end": match.end()},
                })

        metadata = {
            "pii_detected": len(detections),
            "detections": detections,
            "original_hash": hash_text(text),
        }

        return sanitized, metadata

    def is_cloud_safe(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Check if text is safe to send to a cloud LLM.

        Analyzes the text for PII and determines cloud safety.

        Args:
            text: The text to check.

        Returns:
            Tuple of (is_safe, metadata).
        """
        from backend.privacy_guard.domain.value_objects import PII_TYPES

        findings: list[dict[str, Any]] = []
        has_direct_pii = False

        for pii_type in PII_TYPES.values():
            matches = pii_type.matches(text)
            for match in matches:
                entry = {
                    "category": pii_type.category.value,
                    "cloud_safety": pii_type.cloud_safety.value,
                    "position": {"start": match.start(), "end": match.end()},
                }
                findings.append(entry)
                if pii_type.cloud_safety == CloudSafety.NEVER:
                    has_direct_pii = True

        is_safe = not has_direct_pii
        metadata = {
            "is_safe": is_safe,
            "pii_found": len(findings),
            "findings": findings,
        }

        return is_safe, metadata
