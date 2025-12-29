# src/backend/rag_pipeline/agents/preprocessing_agent.py
"""
Agent for preprocessing medical text.
"""

from crewai import LLM

from backend.rag_pipeline.agents.base_agent import AgentConfig, BaseRAGAgent
from backend.rag_pipeline.agents.llm_selector import get_llm_for_agent


class PreprocessingAgent(BaseRAGAgent):
    """
    An agent expert in cleaning and structuring raw medical text for analysis.

    This agent handles:
    - OCR error correction
    - Terminology standardization
    - Text formatting and structure normalization
    """

    AGENT_NAME = "PreprocessingAgent"

    def __init__(self, config: AgentConfig | None = None, llm: LLM | None = None):
        """
        Initialize the PreprocessingAgent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
            llm: Optional pre-configured LLM. If not provided, uses LLM selector.
        """
        # If no LLM provided, get one from the selector
        if llm is None:
            llm = get_llm_for_agent(self.AGENT_NAME)

        super().__init__(config=config, llm=llm)

    def _get_default_config(self) -> AgentConfig:
        """Return the default configuration for PreprocessingAgent."""
        return AgentConfig(
            role="Medical Text Preprocessor",
            goal="Clean and structure raw medical text for analysis.",
            backstory=(
                "You are an expert in medical data processing. Your role is to take "
                "raw, unstructured medical text, such as clinical notes or patient "
                "transcripts, and prepare it for downstream analysis by other agents. "
                "This includes correcting OCR errors, standardizing terminology, and "
                "formatting the text into a clean, readable format."
            ),
            llm_provider="ollama",
            llm_model="llama3.2:latest",  # 2GB - fast, good for text cleanup
            llm_temperature=0.3,  # Lower temperature for consistent preprocessing
            allow_delegation=False,
            verbose=True,
        )


# Backwards compatibility: allow creating with just an llm parameter
def create_preprocessing_agent(llm: LLM | None = None) -> PreprocessingAgent:
    """
    Factory function to create a PreprocessingAgent.

    Args:
        llm: Optional LLM instance. If not provided, uses agent-specific LLM.

    Returns:
        Configured PreprocessingAgent instance.
    """
    return PreprocessingAgent(llm=llm)
