# src/backend/rag_pipeline/agents/summarization_agent.py
"""
Agent for summarizing medical text.
"""

from crewai import Agent


class SummarizationAgent(Agent):
    """
    An agent expert in creating concise and accurate summaries of medical text.
    """

    def __init__(self, llm):
        """
        Initializes the SummarizationAgent.

        Args:
            llm: The language model to be used by the agent.
        """
        super().__init__(
            role="Medical Summarization Specialist",
            goal="Create concise, accurate, and readable summaries of medical text.",
            backstory=(
                "You are an AI agent with a specialization in medical summarization. "
                "You can distill lengthy and complex medical documents into clear and "
                "concise summaries, tailored for different audiences, from clinicians "
                "to patients. Your summaries are designed to be accurate, easy to "
                "understand, and to highlight the most critical information."
            ),
            tools=[],
            llm=llm,
            allow_delegation=False,
            verbose=True,
        )
