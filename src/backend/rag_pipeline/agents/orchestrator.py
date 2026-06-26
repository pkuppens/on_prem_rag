# src/backend/rag_pipeline/agents/orchestrator.py
"""
Compatibility shim — re-exports from backend.medical_agents.orchestrator.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents.orchestrator import *  # noqa: F401, F403
