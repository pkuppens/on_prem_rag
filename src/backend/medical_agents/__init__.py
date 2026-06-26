# src/backend/medical_agents/__init__.py
"""
Medical Agents bounded context.

This package provides specialized AI agents for medical text processing,
each with optimized LLM configurations for their specific roles.
"""

from crewai import LLM

from backend.medical_agents.base_agent import (
    AgentConfig,
    AgentMetrics,
    BaseRAGAgent,
    GuardrailsConfig,
    MemoryHooks,
    PIIGuard,
)
from backend.medical_agents.clinical_extractor import ClinicalExtractorAgent, create_clinical_extractor_agent
from backend.medical_agents.language_assessor import LanguageAssessorAgent, create_language_assessor_agent
from backend.medical_agents.llm_selector import (
    AgentLLMSelector,
    LLMConfig,
    get_llm_for_agent,
    get_llm_selector,
)
from backend.medical_agents.orchestrator import (
    MedicalCrewOrchestrator,
    OrchestrationResult,
    ProcessType,
    TaskDefinition,
    create_medical_orchestrator,
)
from backend.medical_agents.preprocessing_agent import PreprocessingAgent, create_preprocessing_agent
from backend.medical_agents.quality_control_agent import QualityControlAgent, create_quality_control_agent
from backend.medical_agents.summarization_agent import SummarizationAgent, create_summarization_agent

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


def create_medical_crew(
    llm: LLM | None = None,
    session_id: str | None = None,
) -> list[BaseRAGAgent]:
    """
    Create the medical crew with all specialized agents.

    Each agent will use its optimized LLM configuration from the LLM selector
    unless a shared LLM is provided.

    Args:
        llm: Optional shared LLM for all agents. If None, each agent uses
             its agent-specific LLM configuration.
        session_id: Optional session ID for memory management. If provided,
            enables persistent memory across all agents in the crew.

    Returns:
        A list of all agents in the medical crew.
    """
    return [
        PreprocessingAgent(llm=llm, session_id=session_id),
        LanguageAssessorAgent(llm=llm, session_id=session_id),
        ClinicalExtractorAgent(llm=llm, session_id=session_id),
        SummarizationAgent(llm=llm, session_id=session_id),
        QualityControlAgent(llm=llm, session_id=session_id),
    ]
