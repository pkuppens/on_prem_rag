# src/backend/rag_pipeline/agents/quality_control_agent.py
"""
Agent for quality control of medical text analysis.
"""

from crewai import Agent


class QualityControlAgent(Agent):
    """
    An agent expert in ensuring the quality and accuracy of medical text analysis.
    """

    def __init__(self, llm):
        """
        Initializes the QualityControlAgent.

        Args:
            llm: The language model to be used by the agent.
        """
        super().__init__(
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
            tools=[],
            llm=llm,
            allow_delegation=False,
            verbose=True,
        )
