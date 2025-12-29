# src/backend/guardrails/input_guardrails.py
"""Input guardrails for validating user requests.

Provides protection against:
- Jailbreak attempts
- Prompt injection
- Off-topic requests
- PII in input (delegation to privacy_guard)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.guardrails.config_loader import GuardrailsConfig

logger = logging.getLogger(__name__)

# Common jailbreak patterns
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

# Compiled patterns for efficiency
JAILBREAK_REGEX = [re.compile(p, re.IGNORECASE) for p in JAILBREAK_PATTERNS]

# Off-topic patterns (non-medical)
OFF_TOPIC_PATTERNS = [
    r"(tell|write)\s+me\s+a\s+(joke|story|poem)",
    r"what('s|\s+is)\s+the\s+weather",
    r"play\s+(a\s+game|with\s+me)",
    r"help\s+(me\s+)?with\s+(my\s+)?homework",
    r"what\s+is\s+the\s+capital\s+of",
    r"(who|what)\s+(is|was)\s+the\s+(president|king|queen)",
    r"(sing|dance|draw)\s+(a|me|for)",
]

OFF_TOPIC_REGEX = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]


@dataclass
class InputValidationResult:
    """Result of input validation."""

    is_valid: bool
    reason: str = ""
    detected_issues: list[str] = field(default_factory=list)
    sanitized_input: str | None = None
    should_block: bool = False

    @classmethod
    def valid(cls, input_text: str) -> "InputValidationResult":
        """Create a valid result."""
        return cls(is_valid=True, sanitized_input=input_text)

    @classmethod
    def invalid(cls, reason: str, issues: list[str] | None = None) -> "InputValidationResult":
        """Create an invalid result."""
        return cls(
            is_valid=False,
            reason=reason,
            detected_issues=issues or [],
            should_block=True,
        )


class InputGuardrails:
    """Input validation guardrails.

    Validates user input before processing by the agent pipeline.
    """

    def __init__(self, config: "GuardrailsConfig"):
        self.config = config
        self._pii_guard = None
        self._init_pii_guard()

    def _init_pii_guard(self) -> None:
        """Initialize PII guard if available."""
        try:
            from backend.privacy_guard.domain.value_objects import PII_TYPES, PIICategory

            self._pii_types = PII_TYPES
            self._pii_category = PIICategory
            self._pii_guard_available = True
        except ImportError:
            self._pii_guard_available = False
            logger.warning("privacy_guard module not available, PII detection disabled")

    def validate(self, input_text: str, context: dict | None = None) -> InputValidationResult:
        """Validate user input.

        Args:
            input_text: The user's input text
            context: Optional context (e.g., user role, session info)

        Returns:
            InputValidationResult with validation outcome
        """
        if not self.config.enabled:
            return InputValidationResult.valid(input_text)

        # Check for bypass (internal/trusted calls)
        if context and self._should_bypass(context):
            return InputValidationResult.valid(input_text)

        issues = []

        # Check for jailbreak attempts
        if self.config.enable_jailbreak_detection:
            jailbreak_result = self.check_jailbreak(input_text)
            if jailbreak_result.detected_issues:
                issues.extend(jailbreak_result.detected_issues)
                if self.config.audit_logging:
                    logger.warning(f"Jailbreak attempt detected: {jailbreak_result.detected_issues}")
                return InputValidationResult.invalid(
                    "Request blocked: potential jailbreak attempt detected",
                    issues,
                )

        # Check for off-topic requests
        if self.config.enable_topic_filtering:
            topic_result = self.check_topic(input_text)
            if not topic_result.is_valid:
                issues.extend(topic_result.detected_issues)
                if self.config.audit_logging:
                    logger.info(f"Off-topic request detected: {input_text[:100]}...")
                return InputValidationResult.invalid(
                    "Request blocked: topic not related to medical document analysis",
                    issues,
                )

        # Check for PII in input
        if self.config.enable_pii_input_check:
            pii_result = self.check_pii(input_text)
            if pii_result.detected_issues:
                issues.extend(pii_result.detected_issues)
                if self.config.audit_logging:
                    logger.warning(f"PII detected in input: {pii_result.detected_issues}")
                # Don't block, but warn
                return InputValidationResult(
                    is_valid=True,
                    reason="PII detected - proceeding with caution",
                    detected_issues=issues,
                    sanitized_input=input_text,
                    should_block=False,
                )

        return InputValidationResult.valid(input_text)

    def check_jailbreak(self, input_text: str) -> InputValidationResult:
        """Check for jailbreak attempts using pattern matching.

        Args:
            input_text: Text to check

        Returns:
            InputValidationResult with detected jailbreak patterns
        """
        issues = []
        for pattern in JAILBREAK_REGEX:
            match = pattern.search(input_text)
            if match:
                issues.append(f"jailbreak_pattern:{match.group()}")

        if issues:
            return InputValidationResult.invalid("Jailbreak attempt detected", issues)
        return InputValidationResult.valid(input_text)

    def check_topic(self, input_text: str) -> InputValidationResult:
        """Check if the input is on-topic for medical document analysis.

        Args:
            input_text: Text to check

        Returns:
            InputValidationResult indicating if topic is allowed
        """
        # First check for obvious off-topic patterns
        for pattern in OFF_TOPIC_REGEX:
            if pattern.search(input_text):
                return InputValidationResult.invalid(
                    "Off-topic request",
                    ["off_topic:pattern_match"],
                )

        # Check for medical-related keywords
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

        input_lower = input_text.lower()
        has_medical_context = any(kw in input_lower for kw in medical_keywords)

        # If no medical context and it's a substantive request, likely off-topic
        if not has_medical_context and len(input_text.split()) > 5:
            # Check if it's a greeting or simple acknowledgment (allowed)
            simple_patterns = ["hello", "hi", "thanks", "thank you", "yes", "no", "ok"]
            if not any(input_lower.strip().startswith(p) for p in simple_patterns):
                return InputValidationResult.invalid(
                    "Request not related to medical documents",
                    ["off_topic:no_medical_context"],
                )

        return InputValidationResult.valid(input_text)

    def check_pii(self, input_text: str) -> InputValidationResult:
        """Check for PII in input using privacy_guard.

        Args:
            input_text: Text to check

        Returns:
            InputValidationResult with detected PII categories
        """
        if not self._pii_guard_available:
            return InputValidationResult.valid(input_text)

        detected_categories = []
        for category, pii_type in self._pii_types.items():
            matches = pii_type.matches(input_text)
            if matches:
                detected_categories.append(f"pii:{category.value}")

        if detected_categories:
            return InputValidationResult(
                is_valid=True,  # Don't block, but flag
                reason="PII detected in input",
                detected_issues=detected_categories,
                sanitized_input=input_text,
                should_block=False,
            )

        return InputValidationResult.valid(input_text)

    def _should_bypass(self, context: dict) -> bool:
        """Check if request should bypass guardrails.

        Args:
            context: Request context

        Returns:
            True if guardrails should be bypassed
        """
        if not self.config.bypass_internal_calls:
            return False

        source = context.get("source", "")
        return source in self.config.trusted_sources
