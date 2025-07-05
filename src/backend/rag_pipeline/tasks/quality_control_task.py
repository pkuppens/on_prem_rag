# src/backend/rag_pipeline/tasks/quality_control_task.py
"""
Task for quality control of medical text analysis.
"""

from crewai import Task


class QualityControlTask(Task):
    """
    A task for ensuring the quality and accuracy of medical text analysis.
    """

    def __init__(self, agent):
        """
        Initializes the QualityControlTask.

        Args:
            agent: The agent to perform the task.
        """
        super().__init__(
            description=(
                "Review the outputs of the previous analysis steps and verify the "
                "accuracy of the extracted information, the clarity of the summary, "
                "and the overall quality of the analysis. Provide a final quality "
                "assessment."
            ),
            expected_output="A quality control report, including a final assessment.",
            agent=agent,
        )
