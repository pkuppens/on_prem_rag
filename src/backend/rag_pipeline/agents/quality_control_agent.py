# src/backend/rag_pipeline/agents/quality_control_agent.py
"""
Agent for quality control of medical text analysis.
"""

from crewai import LLM

from backend.rag_pipeline.agents.base_agent import AgentConfig, BaseRAGAgent
from backend.rag_pipeline.agents.llm_selector import get_llm_for_agent


class QualityControlAgent(BaseRAGAgent):
    """
    An agent expert in ensuring the quality and accuracy of medical text analysis.

    This agent handles:
    - Output verification and validation
    - Accuracy checking of extracted information
    - Quality assessment of summaries
    - Final review before delivery
    """

    AGENT_NAME = "QualityControlAgent"

    def __init__(self, config: AgentConfig | None = None, llm: LLM | None = None):
        """
        Initialize the QualityControlAgent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
            llm: Optional pre-configured LLM. If not provided, uses LLM selector.
        """
        if llm is None:
            llm = get_llm_for_agent(self.AGENT_NAME)

        super().__init__(config=config, llm=llm)

    def _get_default_config(self) -> AgentConfig:
        """Return the default configuration for QualityControlAgent."""
        return AgentConfig(
            role="Medical Quality Control Inspector",
            goal="Ensure the accuracy and quality of the medical text analysis.",
            backstory=(
                "You are a meticulous AI agent responsible for quality control. "
                "Your function is to review the outputs of other agents, verifying "
                "the accuracy of extracted information, the clarity of summaries, "
                "and the overall quality of the analysis. You are the final checkpoint "
                "before the results are delivered, ensuring that the highest standards "
                "of quality and accuracy are met."
            ),
            llm_provider="ollama",
            llm_model="mistral:latest",  # 4.1GB - reliable for QC tasks
            llm_temperature=0.1,  # Very low temperature for consistent QC
            allow_delegation=False,
            verbose=True,
        )


def create_quality_control_agent(llm: LLM | None = None) -> QualityControlAgent:
    """Factory function to create a QualityControlAgent."""
    return QualityControlAgent(llm=llm)
