# src/backend/rag_pipeline/tasks/extract_clinical_task.py
"""
Task for extracting clinical information from medical text.
"""

from crewai import Task


class ExtractClinicalInfoTask(Task):
    """
    A task for extracting structured clinical information from
    unstructured medical text.
    """

    def __init__(self, agent):
        """
        Initializes the ExtractClinicalInfoTask.

        Args:
            agent: The agent to perform the task.
        """
        super().__init__(
            description=(
                "Extract key clinical entities from the medical text. "
                "This includes diagnoses, medications, procedures, and other "
                "critical clinical data points."
            ),
            expected_output="Structured clinical information in JSON format.",
            agent=agent,
        )
