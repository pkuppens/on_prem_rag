# src/backend/guardrails/actions/security_actions.py
"""Security-related custom actions for NeMo Guardrails.

These actions provide jailbreak detection, topic filtering, and blocked terms checking.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Jailbreak patterns (same as input_guardrails.py)
JAILBREAK_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)",
    r"forget\s+(your|all)\s+(guidelines?|instructions?|rules?)",
    r"you\s+are\s+now\s+(DAN|unfiltered|unrestricted)",
    r"pretend\s+you\s+(have\s+no|don't\s+have)\s+(restrictions?|guidelines?)",
    r"bypass\s+(your|the)\s+safety",
    r"reveal\s+(your|the)\s+system\s+prompt",
    r"what\s+are\s+your\s+(instructions?|guidelines?)",
    r"act\s+as\s+(if\s+you\s+have\s+no|an?\s+unrestricted)",
    r"\[INST\].*system.*\[/INST\]",
    r"<\|im_start\|>system",
    r"###\s*(System|Instruction)",
    r"override\s+(security|safety)",
    r"disable\s+(filters?|guardrails?|safety)",
]

JAILBREAK_REGEX = [re.compile(p, re.IGNORECASE) for p in JAILBREAK_PATTERNS]

# Default blocked terms
DEFAULT_BLOCKED_TERMS = [
    "system prompt",
    "ignore previous",
    "bypass",
    "jailbreak",
]


async def check_jailbreak_action(context: dict[str, Any] | None = None) -> bool:
    """Check if the user message contains jailbreak attempts.

    This action is called from Colang flows to detect jailbreak attempts.

    Args:
        context: The NeMo Guardrails context containing user_message

    Returns:
        True if jailbreak attempt detected, False otherwise
    """
    if context is None:
        return False

    user_message = context.get("user_message", "")
    if not user_message:
        return False

    for pattern in JAILBREAK_REGEX:
        if pattern.search(user_message):
            logger.warning(f"Jailbreak attempt detected: {pattern.pattern}")
            return True

    return False


async def check_topic_action(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Check if the user message is on an allowed topic.

    This action validates that the request is related to medical document analysis.

    Args:
        context: The NeMo Guardrails context containing user_message

    Returns:
        Dict with 'allowed' boolean and 'reason' string
    """
    if context is None:
        return {"allowed": True, "reason": "No context provided"}

    user_message = context.get("user_message", "")
    if not user_message:
        return {"allowed": True, "reason": "Empty message"}

    # Medical-related keywords
    medical_keywords = [
        "medical",
        "clinical",
        "patient",
        "diagnosis",
        "treatment",
        "document",
        "report",
        "record",
        "summary",
        "extract",
        "health",
        "doctor",
        "hospital",
        "medication",
        "symptom",
        "analyze",
        "summarize",
        "review",
        "condition",
        "finding",
    ]

    # Off-topic patterns
    off_topic_patterns = [
        r"(tell|write)\s+me\s+a\s+(joke|story|poem)",
        r"what('s|\s+is)\s+the\s+weather",
        r"play\s+(a\s+game|with\s+me)",
        r"help\s+(me\s+)?with\s+(my\s+)?homework",
        r"what\s+is\s+the\s+capital\s+of",
    ]

    user_lower = user_message.lower()

    # Check for off-topic patterns
    for pattern in off_topic_patterns:
        if re.search(pattern, user_lower, re.IGNORECASE):
            return {
                "allowed": False,
                "reason": "Off-topic request detected",
            }

    # Check for medical context
    has_medical_context = any(kw in user_lower for kw in medical_keywords)

    # Allow simple greetings
    simple_patterns = ["hello", "hi", "thanks", "thank you", "yes", "no", "ok"]
    is_simple = any(user_lower.strip().startswith(p) for p in simple_patterns)

    if has_medical_context or is_simple or len(user_message.split()) <= 5:
        return {"allowed": True, "reason": "Valid request"}

    return {
        "allowed": False,
        "reason": "Request not related to medical document analysis",
    }


async def check_blocked_terms_action(
    text: str = "",
    blocked_terms: list[str] | None = None,
    context: dict[str, Any] | None = None,
) -> bool:
    """Check if text contains blocked terms.

    Args:
        text: Text to check
        blocked_terms: List of blocked terms (uses defaults if not provided)
        context: Optional context

    Returns:
        True if blocked terms found, False otherwise
    """
    if not text and context:
        text = context.get("bot_message", "") or context.get("user_message", "")

    if not text:
        return False

    terms = blocked_terms or DEFAULT_BLOCKED_TERMS
    text_lower = text.lower()

    for term in terms:
        if term.lower() in text_lower:
            logger.warning(f"Blocked term detected: {term}")
            return True

    return False
