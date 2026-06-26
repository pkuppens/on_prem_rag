# src/backend/rag_pipeline/agents/quality_control_agent.py
"""
Compatibility shim — re-exports from backend.medical_agents.quality_control_agent.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents.quality_control_agent import *  # noqa: F401, F403
