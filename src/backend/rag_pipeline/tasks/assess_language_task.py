# src/backend/rag_pipeline/tasks/assess_language_task.py
"""
Task for assessing the language in medical text.
"""

from crewai import Task


class AssessPatientLanguageTask(Task):
    """
    A task for assessing the language of medical text for clarity,
    sentiment, and complexity.
    """

    def __init__(self, agent):
        """
        Initializes the AssessPatientLanguageTask.

        Args:
            agent: The agent to perform the task.
        """
        super().__init__(
            description=(
                "Assess the clarity, sentiment, and complexity of the medical text. "
                "Provide a report on readability, emotional tone, and terminology complexity."
            ),
            expected_output="A report on the language assessment.",
            agent=agent,
        )
