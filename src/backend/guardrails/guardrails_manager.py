# src/backend/guardrails/guardrails_manager.py
"""Unified guardrails manager for the RAG pipeline.

Provides a single interface for all guardrails operations.
Integrates NeMo Guardrails with custom input/output validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from backend.guardrails.config_loader import GuardrailsConfig, get_guardrails_config
from backend.guardrails.input_guardrails import InputGuardrails, InputValidationResult
from backend.guardrails.output_guardrails import OutputGuardrails, OutputValidationResult

logger = logging.getLogger(__name__)

# Track if NeMo Guardrails is available
NEMO_AVAILABLE = False
try:
    from nemoguardrails import LLMRails, RailsConfig

    NEMO_AVAILABLE = True
except ImportError:
    logger.warning("nemoguardrails not available, using fallback guardrails only")


class ValidationStatus(Enum):
    """Status of a validation check."""

    PASSED = "passed"
    BLOCKED = "blocked"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    check_name: str
    status: ValidationStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class GuardrailsResult:
    """Combined result of all guardrails checks."""

    is_allowed: bool
    input_validation: InputValidationResult | None = None
    output_validation: OutputValidationResult | None = None
    nemo_result: dict[str, Any] | None = None
    validations: list[ValidationResult] = field(default_factory=list)
    processing_time_ms: float = 0.0

    @property
    def blocking_reason(self) -> str | None:
        """Get the reason for blocking, if any."""
        if self.is_allowed:
            return None
        if self.input_validation and not self.input_validation.is_valid:
            return self.input_validation.reason
        if self.output_validation and not self.output_validation.is_valid:
            return self.output_validation.reason
        return "Unknown blocking reason"

    @property
    def all_issues(self) -> list[str]:
        """Get all detected issues."""
        issues = []
        if self.input_validation:
            issues.extend(self.input_validation.detected_issues)
        if self.output_validation:
            issues.extend(self.output_validation.detected_issues)
        return issues


class GuardrailsManager:
    """Unified guardrails manager.

    Combines NeMo Guardrails with custom input/output validation.
    Provides a single interface for all guardrails operations.
    """

    def __init__(self, config: GuardrailsConfig | None = None):
        self.config = config or get_guardrails_config()
        self.input_guardrails = InputGuardrails(self.config)
        self.output_guardrails = OutputGuardrails(self.config)
        self._nemo_rails: LLMRails | None = None
        self._init_nemo_rails()

    def _init_nemo_rails(self) -> None:
        """Initialize NeMo Guardrails if available."""
        if not NEMO_AVAILABLE:
            return

        if not self.config.enabled:
            return

        try:
            config_dir = self.config.config_dir
            if config_dir.exists():
                # Load from config directory
                nemo_config = RailsConfig.from_path(str(config_dir))
            else:
                # Use programmatic configuration
                nemo_config = RailsConfig.from_content(config=self.config.to_nemo_config())

            self._nemo_rails = LLMRails(nemo_config)
            self._register_custom_actions()
            logger.info("NeMo Guardrails initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize NeMo Guardrails: {e}")
            self._nemo_rails = None

    def _register_custom_actions(self) -> None:
        """Register custom actions with NeMo Guardrails."""
        if self._nemo_rails is None:
            return

        try:
            from backend.guardrails.actions import (
                audit_action,
                check_blocked_terms_action,
                check_jailbreak_action,
                check_pii_action,
                check_topic_action,
            )

            self._nemo_rails.register_action(check_jailbreak_action, "check_jailbreak_attempt")
            self._nemo_rails.register_action(check_pii_action, "check_pii_in_text")
            self._nemo_rails.register_action(check_topic_action, "check_topic_allowed")
            self._nemo_rails.register_action(check_blocked_terms_action, "check_blocked_terms")
            self._nemo_rails.register_action(audit_action, "audit_guardrail_event")

            logger.debug("Custom actions registered with NeMo Guardrails")

        except Exception as e:
            logger.error(f"Failed to register custom actions: {e}")

    def validate_input(
        self,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> GuardrailsResult:
        """Validate user input before processing.

        Args:
            input_text: The user's input text
            context: Optional context for the request

        Returns:
            GuardrailsResult with validation outcome
        """
        import time

        start_time = time.time()
        validations: list[ValidationResult] = []

        if not self.config.enabled:
            return GuardrailsResult(
                is_allowed=True,
                validations=[
                    ValidationResult(
                        check_name="guardrails_enabled",
                        status=ValidationStatus.SKIPPED,
                        message="Guardrails disabled",
                    )
                ],
            )

        # Run custom input validation
        input_result = self.input_guardrails.validate(input_text, context)

        validations.append(
            ValidationResult(
                check_name="input_validation",
                status=ValidationStatus.PASSED if input_result.is_valid else ValidationStatus.BLOCKED,
                message=input_result.reason,
                details={"issues": input_result.detected_issues},
            )
        )

        # If custom validation failed, don't proceed to NeMo
        if not input_result.is_valid and input_result.should_block:
            processing_time = (time.time() - start_time) * 1000
            return GuardrailsResult(
                is_allowed=False,
                input_validation=input_result,
                validations=validations,
                processing_time_ms=processing_time,
            )

        # Run NeMo Guardrails if available
        nemo_result = None
        if self._nemo_rails is not None:
            try:
                messages = [{"role": "user", "content": input_text}]
                if context:
                    messages.insert(0, {"role": "context", "content": context})

                nemo_response = self._nemo_rails.generate(messages=messages)
                nemo_result = {
                    "response": nemo_response.get("content", ""),
                    "blocked": nemo_response.get("blocked", False),
                }

                validations.append(
                    ValidationResult(
                        check_name="nemo_guardrails",
                        status=ValidationStatus.BLOCKED if nemo_result["blocked"] else ValidationStatus.PASSED,
                        message="NeMo Guardrails check",
                        details=nemo_result,
                    )
                )

                if nemo_result["blocked"]:
                    processing_time = (time.time() - start_time) * 1000
                    return GuardrailsResult(
                        is_allowed=False,
                        input_validation=input_result,
                        nemo_result=nemo_result,
                        validations=validations,
                        processing_time_ms=processing_time,
                    )

            except Exception as e:
                logger.error(f"NeMo Guardrails error: {e}")
                validations.append(
                    ValidationResult(
                        check_name="nemo_guardrails",
                        status=ValidationStatus.ERROR,
                        message=str(e),
                    )
                )

        processing_time = (time.time() - start_time) * 1000
        return GuardrailsResult(
            is_allowed=True,
            input_validation=input_result,
            nemo_result=nemo_result,
            validations=validations,
            processing_time_ms=processing_time,
        )

    def validate_output(
        self,
        output_text: str,
        context: dict[str, Any] | None = None,
    ) -> GuardrailsResult:
        """Validate agent output before returning to user.

        Args:
            output_text: The agent's output text
            context: Optional context for the request

        Returns:
            GuardrailsResult with validation outcome
        """
        import time

        start_time = time.time()
        validations: list[ValidationResult] = []

        if not self.config.enabled:
            return GuardrailsResult(
                is_allowed=True,
                validations=[
                    ValidationResult(
                        check_name="guardrails_enabled",
                        status=ValidationStatus.SKIPPED,
                        message="Guardrails disabled",
                    )
                ],
            )

        # Run custom output validation
        output_result = self.output_guardrails.validate(output_text, context)

        validations.append(
            ValidationResult(
                check_name="output_validation",
                status=ValidationStatus.PASSED if output_result.is_valid else ValidationStatus.BLOCKED,
                message=output_result.reason,
                details={"issues": output_result.detected_issues},
            )
        )

        processing_time = (time.time() - start_time) * 1000
        return GuardrailsResult(
            is_allowed=output_result.is_valid and not output_result.should_block,
            output_validation=output_result,
            validations=validations,
            processing_time_ms=processing_time,
        )

    def generate_safe_response(
        self,
        messages: list[dict[str, str]],
        context: dict[str, Any] | None = None,
    ) -> GuardrailsResult:
        """Generate a response with guardrails protection.

        This method uses NeMo Guardrails for the full request-response cycle.

        Args:
            messages: Conversation messages
            context: Optional context

        Returns:
            GuardrailsResult with the response
        """
        import time

        start_time = time.time()

        if self._nemo_rails is None:
            return GuardrailsResult(
                is_allowed=False,
                validations=[
                    ValidationResult(
                        check_name="nemo_guardrails",
                        status=ValidationStatus.ERROR,
                        message="NeMo Guardrails not available",
                    )
                ],
            )

        try:
            if context:
                messages = [{"role": "context", "content": context}] + messages

            response = self._nemo_rails.generate(messages=messages)

            processing_time = (time.time() - start_time) * 1000
            return GuardrailsResult(
                is_allowed=not response.get("blocked", False),
                nemo_result={
                    "response": response.get("content", ""),
                    "blocked": response.get("blocked", False),
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"NeMo Guardrails generation error: {e}")
            processing_time = (time.time() - start_time) * 1000
            return GuardrailsResult(
                is_allowed=False,
                validations=[
                    ValidationResult(
                        check_name="nemo_generation",
                        status=ValidationStatus.ERROR,
                        message=str(e),
                    )
                ],
                processing_time_ms=processing_time,
            )

    @property
    def is_nemo_available(self) -> bool:
        """Check if NeMo Guardrails is available and initialized."""
        return self._nemo_rails is not None


# Global manager instance
_manager: GuardrailsManager | None = None


def get_guardrails_manager() -> GuardrailsManager:
    """Get the global guardrails manager instance."""
    global _manager
    if _manager is None:
        _manager = GuardrailsManager()
    return _manager
