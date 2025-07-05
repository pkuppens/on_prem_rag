# src/backend/rag_pipeline/agents/__init__.py
"""
Agents for the RAG pipeline.
"""

from .clinical_extractor import ClinicalExtractorAgent
from .language_assessor import LanguageAssessorAgent
from .preprocessing_agent import PreprocessingAgent
from .quality_control_agent import QualityControlAgent
from .summarization_agent import SummarizationAgent


def create_medical_crew(llm):
    """
    Creates the medical crew with all the agents.

    Args:
        llm: The language model to be used by the agents.

    Returns:
        A list of all the agents in the medical crew.
    """
    return [
        PreprocessingAgent(llm),
        LanguageAssessorAgent(llm),
        ClinicalExtractorAgent(llm),
        SummarizationAgent(llm),
        QualityControlAgent(llm),
    ]
