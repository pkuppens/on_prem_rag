# src/backend/rag_pipeline/agents/language_assessor.py
"""
Agent for assessing the language in medical text.
"""

from crewai import Agent


class LanguageAssessorAgent(Agent):
    """
    An agent expert in assessing the language of medical text for clarity,
    sentiment, and complexity.
    """

    def __init__(self, llm):
        """
        Initializes the LanguageAssessorAgent.

        Args:
            llm: The language model to be used by the agent.
        """
        super().__init__(
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
            tools=[],
            llm=llm,
            allow_delegation=False,
            verbose=True,
        )
