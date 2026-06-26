# src/backend/rag_pipeline/agents/clinical_extractor.py
"""
Compatibility shim — re-exports from backend.medical_agents.clinical_extractor.

This module exists for backward compatibility during the DDD extraction.
All code should eventually import from backend.medical_agents directly.
"""

from backend.medical_agents.clinical_extractor import *  # noqa: F401, F403
