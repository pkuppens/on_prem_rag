# src/backend/rag_pipeline/agents/language_assessor.py
"""
Agent for assessing the language in medical text.
"""

from crewai import LLM

from backend.rag_pipeline.agents.base_agent import AgentConfig, BaseRAGAgent
from backend.rag_pipeline.agents.llm_selector import get_llm_for_agent


class LanguageAssessorAgent(BaseRAGAgent):
    """
    An agent expert in assessing the language of medical text for clarity,
    sentiment, and complexity.

    This agent handles:
    - Readability assessment for different audiences
    - Sentiment and emotional tone analysis
    - Terminology complexity evaluation
    """

    AGENT_NAME = "LanguageAssessorAgent"

    def __init__(self, config: AgentConfig | None = None, llm: LLM | None = None):
        """
        Initialize the LanguageAssessorAgent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
            llm: Optional pre-configured LLM. If not provided, uses LLM selector.
        """
        if llm is None:
            llm = get_llm_for_agent(self.AGENT_NAME)

        super().__init__(config=config, llm=llm)

    def _get_default_config(self) -> AgentConfig:
        """Return the default configuration for LanguageAssessorAgent."""
        return AgentConfig(
            role="Medical Language Assessor",
            goal="Assess the clarity, sentiment, and complexity of medical text.",
            backstory=(
                "You are a computational linguist with expertise in medical "
                "communication. Your task is to analyze medical text to evaluate its "
                "readability for patients, identify any emotionally charged language, "
                "and assess the overall complexity of the terminology used. Your "
                "insights help ensure that communications are clear, empathetic, and "
                "appropriate for the intended audience."
            ),
            llm_provider="ollama",
            llm_model="mistral:latest",  # 4.1GB - excellent for language analysis
            llm_temperature=0.3,
            allow_delegation=False,
            verbose=True,
        )


def create_language_assessor_agent(llm: LLM | None = None) -> LanguageAssessorAgent:
    """Factory function to create a LanguageAssessorAgent."""
    return LanguageAssessorAgent(llm=llm)
