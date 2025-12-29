# src/backend/rag_pipeline/agents/orchestrator.py
"""
Crew orchestration for the RAG pipeline.

This module provides orchestration logic for coordinating multiple agents
in sequential and hierarchical processing workflows.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from crewai import LLM, Crew, Process, Task

from backend.rag_pipeline.agents.base_agent import BaseRAGAgent
from backend.rag_pipeline.agents.clinical_extractor import ClinicalExtractorAgent
from backend.rag_pipeline.agents.language_assessor import LanguageAssessorAgent
from backend.rag_pipeline.agents.llm_selector import get_llm_for_agent
from backend.rag_pipeline.agents.preprocessing_agent import PreprocessingAgent
from backend.rag_pipeline.agents.quality_control_agent import QualityControlAgent
from backend.rag_pipeline.agents.summarization_agent import SummarizationAgent

logger = logging.getLogger(__name__)


class ProcessType(Enum):
    """Types of crew processing workflows."""

    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"


@dataclass
class OrchestrationResult:
    """Result from a crew orchestration run."""

    success: bool
    output: Any
    task_outputs: list[Any] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """Definition for a task to be executed by an agent."""

    description: str
    expected_output: str
    agent_name: str
    context_from: list[str] | None = None  # Task dependencies


class MedicalCrewOrchestrator:
    """
    Orchestrates the execution of medical text processing crews.

    Supports:
    - Sequential processing (tasks executed in order)
    - Hierarchical processing (manager coordinates agents)
    - Memory integration across crew executions
    - Error handling and retry logic
    """

    def __init__(
        self,
        process_type: ProcessType = ProcessType.SEQUENTIAL,
        manager_llm: LLM | str | None = None,
        memory: bool = True,
        verbose: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize the orchestrator.

        Args:
            process_type: Type of processing workflow.
            manager_llm: LLM for hierarchical manager (required for hierarchical).
            memory: Enable crew memory (short-term, long-term, entity).
            verbose: Enable verbose output.
            max_retries: Maximum retry attempts for failed tasks.
        """
        self.process_type = process_type
        self.manager_llm = manager_llm
        self.memory = memory
        self.verbose = verbose
        self.max_retries = max_retries

        # Initialize agents
        self._agents: dict[str, BaseRAGAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all medical processing agents."""
        self._agents = {
            "preprocessor": PreprocessingAgent(),
            "language_assessor": LanguageAssessorAgent(),
            "clinical_extractor": ClinicalExtractorAgent(),
            "summarizer": SummarizationAgent(),
            "quality_controller": QualityControlAgent(),
        }
        logger.info(f"Initialized {len(self._agents)} agents")

    def get_agent(self, name: str) -> BaseRAGAgent:
        """Get an agent by name."""
        if name not in self._agents:
            raise KeyError(f"Unknown agent: {name}. Available: {list(self._agents.keys())}")
        return self._agents[name]

    def create_task(
        self,
        description: str,
        expected_output: str,
        agent_name: str,
        context_tasks: list[Task] | None = None,
    ) -> Task:
        """
        Create a task for a specific agent.

        Args:
            description: Task description.
            expected_output: Expected output format.
            agent_name: Name of the agent to execute the task.
            context_tasks: Previous tasks to use as context.

        Returns:
            Configured Task instance.
        """
        agent = self.get_agent(agent_name)

        task_kwargs: dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent.agent,
        }

        if context_tasks:
            task_kwargs["context"] = context_tasks

        return Task(**task_kwargs)

    def create_medical_analysis_crew(
        self,
        document_text: str,
        analysis_focus: str | None = None,
    ) -> Crew:
        """
        Create a crew for comprehensive medical document analysis.

        Args:
            document_text: The medical document text to analyze.
            analysis_focus: Optional specific focus for the analysis.

        Returns:
            Configured Crew ready for execution.
        """
        focus_instruction = f" Focus particularly on: {analysis_focus}" if analysis_focus else ""

        # Task 1: Preprocessing
        preprocessing_task = self.create_task(
            description=f"""
            Preprocess the following medical text for downstream analysis.
            Clean OCR errors, standardize terminology, and format the text.

            Document:
            {document_text}
            """,
            expected_output="Cleaned and structured medical text ready for analysis.",
            agent_name="preprocessor",
        )

        # Task 2: Language Assessment
        language_task = self.create_task(
            description=f"""
            Assess the language in the preprocessed medical text.
            Evaluate readability, sentiment, and terminology complexity.{focus_instruction}
            """,
            expected_output="Language assessment report with readability scores and recommendations.",
            agent_name="language_assessor",
            context_tasks=[preprocessing_task],
        )

        # Task 3: Clinical Extraction
        extraction_task = self.create_task(
            description=f"""
            Extract clinical information from the preprocessed medical text.
            Identify diagnoses, medications, procedures, and key clinical data points.{focus_instruction}
            """,
            expected_output="Structured clinical data extraction with categorized entities.",
            agent_name="clinical_extractor",
            context_tasks=[preprocessing_task],
        )

        # Task 4: Summarization
        summarization_task = self.create_task(
            description=f"""
            Create a comprehensive summary of the medical document analysis.
            Incorporate findings from language assessment and clinical extraction.{focus_instruction}
            """,
            expected_output="Comprehensive medical document summary suitable for clinical review.",
            agent_name="summarizer",
            context_tasks=[language_task, extraction_task],
        )

        # Task 5: Quality Control
        qc_task = self.create_task(
            description="""
            Review all analysis outputs for accuracy and completeness.
            Verify extracted information, check summary quality, and flag any issues.
            """,
            expected_output="Quality control report with verification status and any corrections.",
            agent_name="quality_controller",
            context_tasks=[summarization_task],
        )

        # Build crew configuration
        crew_kwargs: dict[str, Any] = {
            "agents": [agent.agent for agent in self._agents.values()],
            "tasks": [preprocessing_task, language_task, extraction_task, summarization_task, qc_task],
            "verbose": self.verbose,
            "memory": self.memory,
        }

        if self.process_type == ProcessType.SEQUENTIAL:
            crew_kwargs["process"] = Process.sequential
        elif self.process_type == ProcessType.HIERARCHICAL:
            crew_kwargs["process"] = Process.hierarchical
            if self.manager_llm:
                crew_kwargs["manager_llm"] = self.manager_llm
            else:
                # Use a capable LLM for the manager
                crew_kwargs["manager_llm"] = get_llm_for_agent("QualityControlAgent")

        return Crew(**crew_kwargs)

    def run_analysis(
        self,
        document_text: str,
        analysis_focus: str | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> OrchestrationResult:
        """
        Run a complete medical document analysis.

        Args:
            document_text: The medical document text to analyze.
            analysis_focus: Optional specific focus for the analysis.
            inputs: Additional inputs to pass to the crew.

        Returns:
            OrchestrationResult with analysis outputs.
        """
        logger.info(f"Starting medical analysis (process={self.process_type.value})")

        try:
            crew = self.create_medical_analysis_crew(document_text, analysis_focus)

            # Execute the crew
            kickoff_inputs = inputs or {}
            result = crew.kickoff(inputs=kickoff_inputs)

            # Collect agent metrics
            metrics = {}
            for name, agent in self._agents.items():
                agent_metrics = agent.get_metrics()
                metrics[name] = {
                    "llm_calls": agent_metrics.llm_calls,
                    "errors": agent_metrics.errors,
                }

            logger.info("Medical analysis completed successfully")

            return OrchestrationResult(
                success=True,
                output=result,
                task_outputs=[],  # CrewAI handles task outputs internally
                metrics=metrics,
            )

        except Exception as e:
            logger.error(f"Medical analysis failed: {e}")
            return OrchestrationResult(
                success=False,
                output=None,
                errors=[str(e)],
            )

    def run_custom_workflow(
        self,
        tasks: list[TaskDefinition],
        inputs: dict[str, Any] | None = None,
    ) -> OrchestrationResult:
        """
        Run a custom workflow with specified tasks.

        Args:
            tasks: List of task definitions.
            inputs: Additional inputs to pass to the crew.

        Returns:
            OrchestrationResult with workflow outputs.
        """
        logger.info(f"Starting custom workflow with {len(tasks)} tasks")

        try:
            # Build tasks with dependencies
            created_tasks: dict[str, Task] = {}

            for task_def in tasks:
                context_tasks = None
                if task_def.context_from:
                    context_tasks = [created_tasks[dep] for dep in task_def.context_from if dep in created_tasks]

                task = self.create_task(
                    description=task_def.description,
                    expected_output=task_def.expected_output,
                    agent_name=task_def.agent_name,
                    context_tasks=context_tasks,
                )
                created_tasks[task_def.description[:50]] = task  # Use truncated description as key

            # Get unique agents for these tasks
            task_agents = set(t.agent_name for t in tasks)
            agents = [self._agents[name].agent for name in task_agents if name in self._agents]

            crew_kwargs: dict[str, Any] = {
                "agents": agents,
                "tasks": list(created_tasks.values()),
                "verbose": self.verbose,
                "memory": self.memory,
                "process": Process.sequential if self.process_type == ProcessType.SEQUENTIAL else Process.hierarchical,
            }

            if self.process_type == ProcessType.HIERARCHICAL and self.manager_llm:
                crew_kwargs["manager_llm"] = self.manager_llm

            crew = Crew(**crew_kwargs)
            result = crew.kickoff(inputs=inputs or {})

            return OrchestrationResult(
                success=True,
                output=result,
            )

        except Exception as e:
            logger.error(f"Custom workflow failed: {e}")
            return OrchestrationResult(
                success=False,
                output=None,
                errors=[str(e)],
            )


def create_medical_orchestrator(
    process_type: ProcessType = ProcessType.SEQUENTIAL,
    memory: bool = True,
    verbose: bool = True,
) -> MedicalCrewOrchestrator:
    """
    Factory function to create a medical crew orchestrator.

    Args:
        process_type: Type of processing workflow.
        memory: Enable crew memory.
        verbose: Enable verbose output.

    Returns:
        Configured MedicalCrewOrchestrator instance.
    """
    return MedicalCrewOrchestrator(
        process_type=process_type,
        memory=memory,
        verbose=verbose,
    )
