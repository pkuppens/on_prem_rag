# src/backend/rag_pipeline/agents/__init__.py
"""
Compatibility shim — re-exports from backend.medical_agents.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents import *  # noqa: F401, F403
