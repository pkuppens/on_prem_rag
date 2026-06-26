# src/backend/rag_pipeline/agents/preprocessing_agent.py
"""
Compatibility shim — re-exports from backend.medical_agents.preprocessing_agent.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents.preprocessing_agent import *  # noqa: F401, F403
