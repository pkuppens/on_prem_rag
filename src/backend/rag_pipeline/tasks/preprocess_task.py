# src/backend/rag_pipeline/tasks/preprocess_task.py
"""
Task for preprocessing medical text.
"""

from crewai import Task


class PreprocessMedicalTextTask(Task):
    """
    A task for preprocessing raw medical text for analysis.
    """

    def __init__(self, agent):
        """
        Initializes the PreprocessMedicalTextTask.

        Args:
            agent: The agent to perform the task.
        """
        super().__init__(
            description=(
                "Clean and structure the provided medical text. This involves "
                "correcting OCR errors, standardizing terminology, and formatting "
                "the text into a clean, readable format."
            ),
            expected_output="Cleaned and structured medical text.",
            agent=agent,
        )
