# src/backend/guardrails/actions/pii_action.py
"""PII detection action for NeMo Guardrails.

Integrates with the existing privacy_guard module for PII detection.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Track if privacy_guard is available
PII_GUARD_AVAILABLE = False
PII_TYPES = None
PIICategory = None

try:
    from backend.privacy_guard.domain.value_objects import PII_TYPES as _PII_TYPES
    from backend.privacy_guard.domain.value_objects import PIICategory as _PIICategory

    PII_TYPES = _PII_TYPES
    PIICategory = _PIICategory
    PII_GUARD_AVAILABLE = True
except ImportError:
    logger.warning("privacy_guard module not available, PII detection will use fallback")


async def check_pii_action(
    text: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check for PII in text using privacy_guard module.

    This action is called from Colang flows to detect PII.

    Args:
        text: Text to check for PII
        context: Optional NeMo Guardrails context

    Returns:
        Dict with:
            - contains_pii: bool
            - categories: list of detected PII categories
            - should_block: bool (True for sensitive categories)
    """
    if not text and context:
        text = context.get("user_message", "") or context.get("bot_message", "")

    if not text:
        return {
            "contains_pii": False,
            "categories": [],
            "should_block": False,
        }

    if PII_GUARD_AVAILABLE and PII_TYPES is not None:
        return _check_with_privacy_guard(text)
    else:
        return _check_with_fallback(text)


def _check_with_privacy_guard(text: str) -> dict[str, Any]:
    """Check PII using the privacy_guard module."""
    detected_categories = []
    should_block = False

    for category, pii_type in PII_TYPES.items():
        matches = pii_type.matches(text)
        if matches:
            detected_categories.append(category.value)
            # Check if this is a sensitive category that should block
            if hasattr(pii_type, "cloud_safety"):
                from backend.privacy_guard.domain.value_objects import CloudSafety

                if pii_type.cloud_safety == CloudSafety.NEVER:
                    should_block = True

    return {
        "contains_pii": len(detected_categories) > 0,
        "categories": detected_categories,
        "should_block": should_block,
    }


def _check_with_fallback(text: str) -> dict[str, Any]:
    """Fallback PII detection using simple patterns.

    This is used when privacy_guard is not available.
    """
    import re

    # Simple patterns for common PII
    patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+31|0)[\s-]?[1-9](?:[\s-]?\d){8}\b",  # Dutch phone
        "bsn": r"\b\d{9}\b",  # Dutch BSN (simplified)
        "postal_code": r"\b\d{4}\s?[A-Z]{2}\b",  # Dutch postal code
    }

    detected = []
    for category, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            detected.append(category)

    return {
        "contains_pii": len(detected) > 0,
        "categories": detected,
        "should_block": "bsn" in detected,  # BSN should always block
    }
