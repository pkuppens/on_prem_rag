"""Question Answering API endpoints for the RAG pipeline.

This module provides the /ask endpoint as specified in TASK-010.
It implements a FastAPI endpoint that accepts questions and returns
answers with source context.

See STORY-003 for business context and acceptance criteria.
Issue #86: Voice query pipeline - transcribe audio then query.
"""

import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from backend.stt.service import get_stt_service
from backend.stt.transcriber import SUPPORTED_AUDIO_FORMATS

from ..config.llm_config import get_llm_config
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


class VoiceAskResponse(AskResponse):
    """Response for voice→query: RAG answer plus transcription metadata.

    Extends AskResponse with transcription_language, transcription_text,
    and transcription_latency_ms for downstream use and latency tracking.
    """

    transcription_text: str = Field(..., description="Transcribed question text")
    transcription_language: str = Field(..., description="Detected language code (e.g. nl, en)")
    transcription_latency_ms: int = Field(..., description="Transcription duration in milliseconds")


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
        llm_config = get_llm_config()
        logger.info(
            "Ask query",
            question=payload.question,
            strategy=payload.strategy,
            llm_backend=llm_config.backend_model_pair,
        )

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


# Maximum audio file size for voice query (50 MB)
MAX_VOICE_AUDIO_SIZE = 50 * 1024 * 1024


@router.post("/voice", response_model=VoiceAskResponse)
async def ask_voice(audio: UploadFile = File(..., description="Audio file (e.g. WAV, MP3, WebM)")) -> VoiceAskResponse:
    """Voice query: transcribe audio, then run RAG question-answering.

    Accepts audio, transcribes with faster-whisper (no LLM correction for speed),
    then sends the transcribed text to the QA system. Returns RAG answer with
    transcription metadata (language, latency). Target: transcription < 3 s for
    typical 5–10 s clips (Issue #86).
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = Path(audio.filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {extension}. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}",
        )

    audio_data = await audio.read()
    if len(audio_data) > MAX_VOICE_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Audio file too large. Maximum: {MAX_VOICE_AUDIO_SIZE / 1024 / 1024:.0f} MB",
        )

    # Step 1: Transcribe (draft mode, no correction, auto-detect language)
    t0 = time.perf_counter()
    try:
        stt_service = get_stt_service()
        transcription = stt_service.transcribe_only(
            audio_data=audio_data,
            file_extension=extension,
            language=None,  # Auto-detect for multilingual support
        )
    except Exception as e:
        logger.exception("Voice query transcription failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") from e

    transcription_latency_ms = int((time.perf_counter() - t0) * 1000)
    question = (transcription.text or "").strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="No speech detected in audio. Please try again with clearer audio.",
        )

    # Step 2: Run RAG question-answering (voice->text->retrieve chunks->generate answer)
    try:
        get_metrics().record_query()
        llm_config = get_llm_config()
        logger.info(
            "Voice RAG flow: voice->text [transcribe]",
            question=question[:80],
            language=transcription.language,
            transcribe_ms=transcription_latency_ms,
        )

        result = qa_system.ask_question(
            question=question,
            top_k=5,
            similarity_threshold=0.5,  # Lower than text ask to improve recall for voice queries
            strategy="hybrid",  # Hybrid matches text /ask default; more robust than dense-only
        )

        logger.info(
            "Voice RAG flow: retrieve->generate",
            chunks=result["chunks_retrieved"],
            confidence=result["confidence"],
        )
        return VoiceAskResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            chunks_retrieved=result["chunks_retrieved"],
            average_similarity=result["average_similarity"],
            transcription_text=question,
            transcription_language=transcription.language or "unknown",
            transcription_latency_ms=transcription_latency_ms,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ModelNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LLM model not available",
                "model": e.model_name,
                "remediation": [
                    f"Pull the model: ollama pull {e.model_name}",
                    "List available models: ollama list",
                ],
            },
        ) from e
    except Exception as e:
        logger.error("Voice ask failed", question=question[:80], error=str(e))
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
