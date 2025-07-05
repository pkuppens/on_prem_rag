# src/backend/rag_pipeline/tasks/summarize_task.py
"""
Task for summarizing medical text.
"""

from crewai import Task


class GenerateSummaryTask(Task):
    """
    A task for creating concise and accurate summaries of medical text.
    """

    def __init__(self, agent):
        """
        Initializes the GenerateSummaryTask.

        Args:
            agent: The agent to perform the task.
        """
        super().__init__(
            description=(
                "Create a concise, accurate, and readable summary of the medical text. "
                "The summary should be tailored for a clinical audience and highlight "
                "the most critical information."
            ),
            expected_output="A concise and accurate summary of the medical text.",
            agent=agent,
        )
