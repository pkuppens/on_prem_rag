# src/backend/rag_pipeline/main.py
"""
Main entry point for the RAG pipeline.
"""

from crewai import Crew

from backend.rag_pipeline.agents import create_medical_crew
from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
from backend.rag_pipeline.core.rag_system import LocalRAGSystem
from backend.rag_pipeline.tasks import (
    AssessPatientLanguageTask,
    ExtractClinicalInfoTask,
    GenerateSummaryTask,
    PreprocessMedicalTextTask,
    QualityControlTask,
)


def process_medical_conversation(text: str):
    """
    Processes a medical conversation through the RAG pipeline.

    Args:
        text: The medical conversation to process.

    Returns:
        The result of the crew's work.
    """
    params = get_param_set(DEFAULT_PARAM_SET_NAME)
    rag_system = LocalRAGSystem(params)
    llm = rag_system._setup_llm()

    agents = create_medical_crew(llm)

    preprocessing_agent = agents[0]
    language_assessor_agent = agents[1]
    clinical_extractor_agent = agents[2]
    summarization_agent = agents[3]
    quality_control_agent = agents[4]

    preprocess_task = PreprocessMedicalTextTask(preprocessing_agent)
    assess_language_task = AssessPatientLanguageTask(language_assessor_agent)
    extract_clinical_task = ExtractClinicalInfoTask(clinical_extractor_agent)
    summarize_task = GenerateSummaryTask(summarization_agent)
    quality_control_task = QualityControlTask(quality_control_agent)

    crew = Crew(
        agents=agents,
        tasks=[
            preprocess_task,
            assess_language_task,
            extract_clinical_task,
            summarize_task,
            quality_control_task,
        ],
        verbose=True,
    )

    result = crew.kickoff(inputs={"text": text})
    return result


if __name__ == "__main__":
    # Example usage
    sample_text = "The patient complains of a persistent cough and fever."
    result = process_medical_conversation(sample_text)
    print(result)
