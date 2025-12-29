# src/backend/guardrails/config_loader.py
"""Configuration loader for NeMo Guardrails.

Loads configuration from YAML files and environment variables.
Supports both file-based and programmatic configuration.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GuardrailsConfig:
    """Configuration for NeMo Guardrails integration."""

    # Enable/disable guardrails
    enabled: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_ENABLED", "true").lower() == "true")

    # Ollama configuration
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))

    # Config directory path
    config_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "GUARDRAILS_CONFIG_DIR",
                str(Path(__file__).parent / "config"),
            )
        )
    )

    # Input guardrails settings
    enable_jailbreak_detection: bool = field(
        default_factory=lambda: os.getenv("GUARDRAILS_JAILBREAK_DETECTION", "true").lower() == "true"
    )
    enable_topic_filtering: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_TOPIC_FILTERING", "true").lower() == "true")
    enable_pii_input_check: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_PII_INPUT_CHECK", "true").lower() == "true")

    # Output guardrails settings
    enable_output_safety: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_OUTPUT_SAFETY", "true").lower() == "true")
    enable_pii_output_check: bool = field(
        default_factory=lambda: os.getenv("GUARDRAILS_PII_OUTPUT_CHECK", "true").lower() == "true"
    )
    enable_blocked_terms: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_BLOCKED_TERMS", "true").lower() == "true")

    # Blocked terms list
    blocked_terms: list[str] = field(
        default_factory=lambda: os.getenv(
            "GUARDRAILS_BLOCKED_TERMS_LIST",
            "system prompt,ignore previous,bypass,jailbreak",
        ).split(",")
    )

    # Allowed topics for the medical domain
    allowed_topics: list[str] = field(
        default_factory=lambda: [
            "medical document analysis",
            "clinical information extraction",
            "medical summarization",
            "patient records",
            "medical terminology",
        ]
    )

    # Audit logging
    audit_logging: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_AUDIT_LOGGING", "true").lower() == "true")

    # Performance settings
    timeout_seconds: float = field(default_factory=lambda: float(os.getenv("GUARDRAILS_TIMEOUT", "30.0")))

    # Bypass settings for internal/trusted calls
    bypass_internal_calls: bool = field(default_factory=lambda: os.getenv("GUARDRAILS_BYPASS_INTERNAL", "true").lower() == "true")
    trusted_sources: list[str] = field(
        default_factory=lambda: os.getenv(
            "GUARDRAILS_TRUSTED_SOURCES",
            "internal,localhost,127.0.0.1",
        ).split(",")
    )

    def to_nemo_config(self) -> dict[str, Any]:
        """Convert to NeMo Guardrails configuration dict."""
        return {
            "models": [
                {
                    "type": "main",
                    "engine": "ollama",
                    "model": self.ollama_model,
                    "parameters": {
                        "base_url": self.ollama_base_url,
                        "temperature": 0.1,
                    },
                }
            ],
            "rails": {
                "input": {
                    "flows": self._get_input_flows(),
                },
                "output": {
                    "flows": self._get_output_flows(),
                },
            },
        }

    def _get_input_flows(self) -> list[str]:
        """Get enabled input flows."""
        flows = []
        if self.enable_jailbreak_detection:
            flows.append("check jailbreak")
            flows.append("self check input")
        if self.enable_pii_input_check:
            flows.append("check pii input")
        if self.enable_topic_filtering:
            flows.append("check topic allowed")
        return flows

    def _get_output_flows(self) -> list[str]:
        """Get enabled output flows."""
        flows = []
        if self.enable_output_safety:
            flows.append("self check output")
        if self.enable_pii_output_check:
            flows.append("check pii output")
        if self.enable_blocked_terms:
            flows.append("check blocked terms")
        return flows


# Global configuration instance
_config: GuardrailsConfig | None = None


def get_guardrails_config() -> GuardrailsConfig:
    """Get the global guardrails configuration."""
    global _config
    if _config is None:
        _config = GuardrailsConfig()
    return _config


def set_guardrails_config(config: GuardrailsConfig) -> None:
    """Set the global guardrails configuration."""
    global _config
    _config = config
