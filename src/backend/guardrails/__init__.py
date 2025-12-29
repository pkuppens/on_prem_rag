# src/backend/guardrails/__init__.py
"""NeMo Guardrails integration for the RAG pipeline.

Provides input validation, output filtering, and safety rails for the agent framework.
Integrates with existing privacy_guard and access_control modules.

Features:
- Input validation (topic filtering, jailbreak detection, PII screening)
- Output validation (safety filtering, PII protection)
- Custom actions for integration with existing security modules
- FastAPI middleware for request/response filtering
"""

from backend.guardrails.config_loader import (
    GuardrailsConfig,
    get_guardrails_config,
    set_guardrails_config,
)
from backend.guardrails.guardrails_manager import (
    GuardrailsManager,
    GuardrailsResult,
    ValidationResult,
    get_guardrails_manager,
)
from backend.guardrails.input_guardrails import InputGuardrails
from backend.guardrails.output_guardrails import OutputGuardrails

__all__ = [
    # Configuration
    "GuardrailsConfig",
    "get_guardrails_config",
    "set_guardrails_config",
    # Manager
    "GuardrailsManager",
    "GuardrailsResult",
    "ValidationResult",
    "get_guardrails_manager",
    # Components
    "InputGuardrails",
    "OutputGuardrails",
]
