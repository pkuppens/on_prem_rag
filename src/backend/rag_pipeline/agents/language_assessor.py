# src/backend/rag_pipeline/agents/language_assessor.py
"""
Compatibility shim — re-exports from backend.medical_agents.language_assessor.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents.language_assessor import *  # noqa: F401, F403
