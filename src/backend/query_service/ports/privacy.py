"""IPrivacySanitizer port — interface for Privacy Guard BC.

The Query Service uses this port to sanitize user queries for PII
before sending them to the retrieval system or cloud LLM providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IPrivacySanitizer(ABC):
    """Port for PII detection and sanitization.

    Implementations connect to the Privacy Guard BC to detect and
    remove PII from user queries before they reach retrieval or LLM.
    """

    @abstractmethod
    def sanitize(self, text: str, scope: str | None = None) -> tuple[str, dict[str, Any]]:
        """Sanitize text by removing or anonymizing PII.

        Args:
            text: The text to sanitize.
            scope: Optional data scope for contextual sanitization.

        Returns:
            Tuple of (sanitized_text, metadata_dict) where metadata
            includes PII detection results for audit logging.
        """
        ...

    @abstractmethod
    def is_cloud_safe(self, text: str) -> tuple[bool, dict[str, Any]]:
        """Check if text is safe to send to a cloud LLM.

        Args:
            text: The text to check.

        Returns:
            Tuple of (is_safe, metadata_dict).
        """
        ...
