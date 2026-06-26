# src/backend/rag_pipeline/agents/llm_selector.py
"""
Compatibility shim — re-exports from backend.medical_agents.llm_selector.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents.llm_selector import *  # noqa: F401, F403
