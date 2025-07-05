# src/backend/rag_pipeline/agents/preprocessing_agent.py
"""
Agent for preprocessing medical text.
"""

from crewai import Agent


class PreprocessingAgent(Agent):
    """
    An agent expert in cleaning and structuring raw medical text for analysis.
    """

    def __init__(self, llm):
        """
        Initializes the PreprocessingAgent.

        Args:
            llm: The language model to be used by the agent.
        """
        super().__init__(
            role="Medical Text Preprocessor",
            goal="Clean and structure raw medical text for analysis.",
            backstory=(
                "You are an expert in medical data processing. Your role is to take "
                "raw, unstructured medical text, such as clinical notes or patient "
                "transcripts, and prepare it for downstream analysis by other agents. "
                "This includes correcting OCR errors, standardizing terminology, and "
                "formatting the text into a clean, readable format."
            ),
            tools=[],
            llm=llm,
            allow_delegation=False,
            verbose=True,
        )
