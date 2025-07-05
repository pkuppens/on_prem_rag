# src/backend/rag_pipeline/agents/clinical_extractor.py
"""
Agent for extracting clinical information from medical text.
"""

from crewai import Agent


class ClinicalExtractorAgent(Agent):
    """
    An agent expert in extracting structured clinical information from
    unstructured medical text.
    """

    def __init__(self, llm):
        """
        Initializes the ClinicalExtractorAgent.

        Args:
            llm: The language model to be used by the agent.
        """
        super().__init__(
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
            tools=[],
            llm=llm,
            allow_delegation=False,
            verbose=True,
        )
