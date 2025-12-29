# src/backend/rag_pipeline/agents/__init__.py
"""
Agents for the RAG pipeline.

This module provides specialized AI agents for medical text processing,
each with optimized LLM configurations for their specific roles.
"""

from crewai import LLM

from .base_agent import (
    AgentConfig,
    AgentMetrics,
    BaseRAGAgent,
    GuardrailsConfig,
    MemoryHooks,
    PIIGuard,
)
from .clinical_extractor import ClinicalExtractorAgent, create_clinical_extractor_agent
from .language_assessor import LanguageAssessorAgent, create_language_assessor_agent
from .llm_selector import (
    AgentLLMSelector,
    LLMConfig,
    get_llm_for_agent,
    get_llm_selector,
)
from .orchestrator import (
    MedicalCrewOrchestrator,
    OrchestrationResult,
    ProcessType,
    TaskDefinition,
    create_medical_orchestrator,
)
from .preprocessing_agent import PreprocessingAgent, create_preprocessing_agent
from .quality_control_agent import QualityControlAgent, create_quality_control_agent
from .summarization_agent import SummarizationAgent, create_summarization_agent

__all__ = [
    # Base classes
    "BaseRAGAgent",
    "AgentConfig",
    "AgentMetrics",
    "MemoryHooks",
    # Guardrails
    "GuardrailsConfig",
    "PIIGuard",
    # LLM Selection
    "AgentLLMSelector",
    "LLMConfig",
    "get_llm_for_agent",
    "get_llm_selector",
    # Agent classes
    "PreprocessingAgent",
    "LanguageAssessorAgent",
    "ClinicalExtractorAgent",
    "SummarizationAgent",
    "QualityControlAgent",
    # Factory functions
    "create_preprocessing_agent",
    "create_language_assessor_agent",
    "create_clinical_extractor_agent",
    "create_summarization_agent",
    "create_quality_control_agent",
    "create_medical_crew",
    # Orchestration
    "MedicalCrewOrchestrator",
    "OrchestrationResult",
    "ProcessType",
    "TaskDefinition",
    "create_medical_orchestrator",
]


def create_medical_crew(llm: LLM | None = None) -> list[BaseRAGAgent]:
    """
    Create the medical crew with all specialized agents.

    Each agent will use its optimized LLM configuration from the LLM selector
    unless a shared LLM is provided.

    Args:
        llm: Optional shared LLM for all agents. If None, each agent uses
             its agent-specific LLM configuration.

    Returns:
        A list of all agents in the medical crew.
    """
    return [
        PreprocessingAgent(llm=llm),
        LanguageAssessorAgent(llm=llm),
        ClinicalExtractorAgent(llm=llm),
        SummarizationAgent(llm=llm),
        QualityControlAgent(llm=llm),
    ]
