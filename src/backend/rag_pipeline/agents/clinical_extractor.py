# src/backend/rag_pipeline/agents/clinical_extractor.py
"""
Agent for extracting clinical information from medical text.
"""

from crewai import LLM

from backend.rag_pipeline.agents.base_agent import AgentConfig, BaseRAGAgent
from backend.rag_pipeline.agents.llm_selector import get_llm_for_agent


class ClinicalExtractorAgent(BaseRAGAgent):
    """
    An agent expert in extracting structured clinical information from
    unstructured medical text.

    This agent handles:
    - Diagnosis identification and categorization
    - Medication extraction
    - Procedure identification
    - Clinical data point extraction
    """

    AGENT_NAME = "ClinicalExtractorAgent"

    def __init__(self, config: AgentConfig | None = None, llm: LLM | None = None):
        """
        Initialize the ClinicalExtractorAgent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
            llm: Optional pre-configured LLM. If not provided, uses LLM selector.
        """
        if llm is None:
            llm = get_llm_for_agent(self.AGENT_NAME)

        super().__init__(config=config, llm=llm)

    def _get_default_config(self) -> AgentConfig:
        """Return the default configuration for ClinicalExtractorAgent."""
        return AgentConfig(
            role="Clinical Information Extractor",
            goal="Extract key clinical entities from medical text.",
            backstory=(
                "You are a highly specialized AI agent trained to understand and "
                "extract structured information from unstructured medical documents. "
                "Your expertise lies in identifying and categorizing diagnoses, "
                "medications, procedures, and other critical clinical data points. "
                "Your work is essential for building structured patient records and "
                "enabling data-driven clinical insights."
            ),
            llm_provider="ollama",
            llm_model="deepseek-r1:latest",  # 4.7GB - reasoning model for extraction
            llm_temperature=0.2,  # Low temperature for accuracy
            allow_delegation=False,
            verbose=True,
        )


def create_clinical_extractor_agent(llm: LLM | None = None) -> ClinicalExtractorAgent:
    """Factory function to create a ClinicalExtractorAgent."""
    return ClinicalExtractorAgent(llm=llm)
