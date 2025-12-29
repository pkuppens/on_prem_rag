# src/backend/guardrails/output_guardrails.py
"""Output guardrails for validating agent responses.

Provides protection against:
- Unsafe or harmful content
- PII leakage in responses
- Blocked terms
- Medical advice (should not be given)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.guardrails.config_loader import GuardrailsConfig

logger = logging.getLogger(__name__)

# Patterns indicating medical advice (should be blocked)
MEDICAL_ADVICE_PATTERNS = [
    r"you\s+should\s+(take|start|stop|avoid)\s+\w+",
    r"I\s+recommend\s+(taking|starting|stopping)",
    r"(take|use)\s+\d+\s*(mg|ml|tablet|pill)",
    r"diagnosis\s+is\s+likely",
    r"you\s+(likely|probably)\s+have",
    r"this\s+indicates\s+you\s+have",
]

MEDICAL_ADVICE_REGEX = [re.compile(p, re.IGNORECASE) for p in MEDICAL_ADVICE_PATTERNS]

# System information patterns (should be blocked)
SYSTEM_INFO_PATTERNS = [
    r"my\s+system\s+prompt\s+is",
    r"my\s+instructions?\s+(are|say)",
    r"I\s+(am|was)\s+programmed\s+to",
    r"here\s+is\s+my\s+(system\s+prompt|instructions?)",
]

SYSTEM_INFO_REGEX = [re.compile(p, re.IGNORECASE) for p in SYSTEM_INFO_PATTERNS]


@dataclass
class OutputValidationResult:
    """Result of output validation."""

    is_valid: bool
    reason: str = ""
    detected_issues: list[str] = field(default_factory=list)
    sanitized_output: str | None = None
    should_block: bool = False

    @classmethod
    def valid(cls, output_text: str) -> "OutputValidationResult":
        """Create a valid result."""
        return cls(is_valid=True, sanitized_output=output_text)

    @classmethod
    def invalid(cls, reason: str, issues: list[str] | None = None) -> "OutputValidationResult":
        """Create an invalid result."""
        return cls(
            is_valid=False,
            reason=reason,
            detected_issues=issues or [],
            should_block=True,
        )


class OutputGuardrails:
    """Output validation guardrails.

    Validates agent output before returning to user.
    """

    def __init__(self, config: "GuardrailsConfig"):
        self.config = config
        self._pii_guard_available = False
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

    def validate(self, output_text: str, context: dict | None = None) -> OutputValidationResult:
        """Validate agent output.

        Args:
            output_text: The agent's output text
            context: Optional context (e.g., original request, agent role)

        Returns:
            OutputValidationResult with validation outcome
        """
        if not self.config.enabled:
            return OutputValidationResult.valid(output_text)

        # Check for bypass (internal calls)
        if context and self._should_bypass(context):
            return OutputValidationResult.valid(output_text)

        issues = []

        # Check for blocked terms
        if self.config.enable_blocked_terms:
            blocked_result = self.check_blocked_terms(output_text)
            if blocked_result.detected_issues:
                issues.extend(blocked_result.detected_issues)
                if self.config.audit_logging:
                    logger.warning(f"Blocked terms in output: {blocked_result.detected_issues}")
                return OutputValidationResult.invalid(
                    "Response blocked: contains prohibited content",
                    issues,
                )

        # Check for system information leakage
        system_leak_result = self.check_system_leakage(output_text)
        if system_leak_result.detected_issues:
            issues.extend(system_leak_result.detected_issues)
            if self.config.audit_logging:
                logger.warning("System information leakage detected in output")
            return OutputValidationResult.invalid(
                "Response blocked: potential system information leakage",
                issues,
            )

        # Check for medical advice
        if self.config.enable_output_safety:
            advice_result = self.check_medical_advice(output_text)
            if advice_result.detected_issues:
                issues.extend(advice_result.detected_issues)
                if self.config.audit_logging:
                    logger.warning("Medical advice detected in output")
                return OutputValidationResult.invalid(
                    "Response blocked: contains medical advice",
                    issues,
                )

        # Check for PII in output
        if self.config.enable_pii_output_check:
            pii_result = self.check_pii(output_text)
            if pii_result.detected_issues:
                issues.extend(pii_result.detected_issues)
                if self.config.audit_logging:
                    logger.warning(f"PII detected in output: {pii_result.detected_issues}")
                return OutputValidationResult.invalid(
                    "Response blocked: contains sensitive personal information",
                    issues,
                )

        return OutputValidationResult.valid(output_text)

    def check_blocked_terms(self, output_text: str) -> OutputValidationResult:
        """Check for blocked terms in output.

        Args:
            output_text: Text to check

        Returns:
            OutputValidationResult with detected blocked terms
        """
        output_lower = output_text.lower()
        detected = []

        for term in self.config.blocked_terms:
            if term.lower() in output_lower:
                detected.append(f"blocked_term:{term}")

        if detected:
            return OutputValidationResult.invalid("Blocked terms detected", detected)
        return OutputValidationResult.valid(output_text)

    def check_system_leakage(self, output_text: str) -> OutputValidationResult:
        """Check for system prompt/instruction leakage.

        Args:
            output_text: Text to check

        Returns:
            OutputValidationResult with detected leakage patterns
        """
        issues = []
        for pattern in SYSTEM_INFO_REGEX:
            match = pattern.search(output_text)
            if match:
                issues.append(f"system_leak:{match.group()[:30]}...")

        if issues:
            return OutputValidationResult.invalid("System information leakage", issues)
        return OutputValidationResult.valid(output_text)

    def check_medical_advice(self, output_text: str) -> OutputValidationResult:
        """Check for medical advice in output.

        The system should not provide medical advice, only analyze documents.

        Args:
            output_text: Text to check

        Returns:
            OutputValidationResult with detected advice patterns
        """
        issues = []
        for pattern in MEDICAL_ADVICE_REGEX:
            match = pattern.search(output_text)
            if match:
                issues.append(f"medical_advice:{match.group()[:30]}...")

        if issues:
            return OutputValidationResult.invalid("Medical advice detected", issues)
        return OutputValidationResult.valid(output_text)

    def check_pii(self, output_text: str) -> OutputValidationResult:
        """Check for PII in output using privacy_guard.

        Args:
            output_text: Text to check

        Returns:
            OutputValidationResult with detected PII categories
        """
        if not self._pii_guard_available:
            return OutputValidationResult.valid(output_text)

        detected_categories = []
        for category, pii_type in self._pii_types.items():
            matches = pii_type.matches(output_text)
            if matches:
                detected_categories.append(f"pii:{category.value}")

        if detected_categories:
            return OutputValidationResult.invalid(
                "PII detected in output",
                detected_categories,
            )

        return OutputValidationResult.valid(output_text)

    def _should_bypass(self, context: dict) -> bool:
        """Check if output validation should be bypassed.

        Args:
            context: Request context

        Returns:
            True if guardrails should be bypassed
        """
        if not self.config.bypass_internal_calls:
            return False

        source = context.get("source", "")
        return source in self.config.trusted_sources
