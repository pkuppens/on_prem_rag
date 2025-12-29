# src/backend/rag_pipeline/agents/summarization_agent.py
"""
Agent for summarizing medical text.
"""

from crewai import LLM

from backend.rag_pipeline.agents.base_agent import AgentConfig, BaseRAGAgent
from backend.rag_pipeline.agents.llm_selector import get_llm_for_agent


class SummarizationAgent(BaseRAGAgent):
    """
    An agent expert in creating concise and accurate summaries of medical text.

    This agent handles:
    - Document summarization for different audiences
    - Key information extraction
    - Adaptive summary length and detail level
    """

    AGENT_NAME = "SummarizationAgent"

    def __init__(
        self,
        config: AgentConfig | None = None,
        llm: LLM | None = None,
        session_id: str | None = None,
    ):
        """
        Initialize the SummarizationAgent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
            llm: Optional pre-configured LLM. If not provided, uses LLM selector.
            session_id: Optional session ID for memory management.
        """
        if llm is None:
            llm = get_llm_for_agent(self.AGENT_NAME)

        super().__init__(config=config, llm=llm, session_id=session_id)

    def _get_default_config(self) -> AgentConfig:
        """Return the default configuration for SummarizationAgent."""
        return AgentConfig(
            role="Medical Summarization Specialist",
            goal="Create concise, accurate, and readable summaries of medical text.",
            backstory=(
                "You are an AI agent with a specialization in medical summarization. "
                "You can distill lengthy and complex medical documents into clear and "
                "concise summaries, tailored for different audiences, from clinicians "
                "to patients. Your summaries are designed to be accurate, easy to "
                "understand, and to highlight the most critical information."
            ),
            llm_provider="ollama",
            llm_model="llama3.1:latest",  # 4.7GB - good balance for summarization
            llm_temperature=0.5,
            allow_delegation=False,
            verbose=True,
        )


def create_summarization_agent(llm: LLM | None = None) -> SummarizationAgent:
    """Factory function to create a SummarizationAgent."""
    return SummarizationAgent(llm=llm)
