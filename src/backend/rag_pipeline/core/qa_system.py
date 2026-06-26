"""Compatibility shim — re-exports QASystem from the Query Service BC.

This module was moved to src/backend/query_service/application/query_orchestrator.py.
Keeping this file for backward compatibility during the phased migration.
"""

from __future__ import annotations

from typing import Any

from backend.llm_gateway.domain.interfaces import LLMProvider
from backend.query_service.application.query_orchestrator import QueryOrchestrator
from backend.query_service.application.query_orchestrator import (
    QueryOrchestrator as QASystem,
)

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)

__all__ = ["QASystem", "QueryOrchestrator"]

# Keep the original module logger for backward-compatible log handles
# QASystem is an alias to QueryOrchestrator for backward compatibility
