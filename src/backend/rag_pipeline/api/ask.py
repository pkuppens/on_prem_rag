"""Question Answering API endpoints for the RAG pipeline.

This module provides the /ask endpoint as specified in TASK-010.
It implements a FastAPI endpoint that accepts questions and returns
answers with source context.

See STORY-003 for business context and acceptance criteria.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..core.llm_providers import ModelNotFoundError
from ..core.qa_system import QASystem
from ..utils.logging import StructuredLogger
from .metrics import get_metrics

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/ask", tags=["question-answering"])

# Initialize QA system
qa_system = QASystem()


VALID_STRATEGIES = ("dense", "sparse", "hybrid", "bm25")


class AskRequest(BaseModel):
    """Request payload for the ask endpoint.

    Attributes:
        question: The question to ask about uploaded documents
        top_k: Optional number of chunks to retrieve (default: 5)
        similarity_threshold: Optional minimum similarity score (default: 0.7)
        strategy: Optional retrieval strategy (dense, sparse, hybrid, bm25).
            When omitted, uses RETRIEVAL_STRATEGY env var, then parameter set default.
    """

    question: str = Field(..., min_length=1, description="The question to ask")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    strategy: str | None = Field(
        default=None,
        description="Retrieval strategy: dense, sparse, hybrid, or bm25. Omit to use server default.",
    )

    @field_validator("strategy", mode="after")
    @classmethod
    def validate_strategy(cls, v: str | None) -> str | None:
        """Normalize and validate strategy when provided."""
        if v is None:
            return v
        s = v.lower().strip()
        if s not in VALID_STRATEGIES:
            raise ValueError(f"strategy must be one of {VALID_STRATEGIES}, got {v!r}")
        return s


class AskResponse(BaseModel):
    """Response payload for the ask endpoint.

    Attributes:
        answer: The generated answer text
        sources: List of source documents with metadata
        confidence: Confidence level (high/medium/low)
        chunks_retrieved: Number of chunks used for the answer
        average_similarity: Average similarity score of retrieved chunks
    """

    answer: str
    sources: list[dict]
    confidence: str
    chunks_retrieved: int
    average_similarity: float


@router.post("", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    """Ask a question about uploaded documents and get an answer with sources.

    This endpoint implements TASK-010: Create Question Answering API Endpoint.
    It accepts a question string and returns an answer payload with source context.

    Args:
        payload: The ask request containing the question and optional parameters

    Returns:
        AskResponse containing the answer, sources, and metadata

    Raises:
        HTTPException: If question is empty or processing fails
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")

    try:
        get_metrics().record_query()
        logger.info("Processing question", question=payload.question, strategy=payload.strategy)

        # Use QA system to answer the question
        result = qa_system.ask_question(
            question=payload.question,
            top_k=payload.top_k,
            similarity_threshold=payload.similarity_threshold,
            strategy=payload.strategy,
        )

        # Create response
        response = AskResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            chunks_retrieved=result["chunks_retrieved"],
            average_similarity=result["average_similarity"],
        )

        logger.info(
            "Question answered successfully",
            question=payload.question,
            answer_length=len(result["answer"]),
            confidence=result["confidence"],
        )

        return response

    except ValueError as e:
        logger.warning("Invalid request", question=payload.question, error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e

    except ModelNotFoundError as e:
        logger.warning(
            "LLM model not available",
            model=e.model_name,
            host=e.host,
            error=str(e),
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM model not available",
                "model": e.model_name,
                "remediation": [
                    f"Pull the model: ollama pull {e.model_name}",
                    "Or set OLLAMA_MODEL to an available model (e.g. llama3.2:1b)",
                    "List available models: ollama list",
                ],
                "raw_error": e.raw_error[:200] if e.raw_error else None,
            },
        ) from e

    except Exception as e:
        logger.error("Error during question answering", question=payload.question, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}") from e


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint for the QA system.

    Returns:
        Dictionary containing health status
    """
    try:
        # Check if LLM provider is healthy
        llm_healthy = await qa_system.llm_provider.health_check()

        return {
            "status": "healthy" if llm_healthy else "degraded",
            "llm_provider": "available" if llm_healthy else "unavailable",
            "vector_store": "available",
        }

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}
