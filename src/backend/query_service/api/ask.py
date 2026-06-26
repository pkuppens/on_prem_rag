"""Question Answering API endpoints for the Query Service.

Same URL paths as the original rag_pipeline/api/ask.py for backward compatibility.
Implements the /ask endpoint as specified in TASK-010.
"""

import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from backend.query_service.application.query_orchestrator import QueryOrchestrator
from backend.rag_pipeline.config.llm_config import get_llm_config
from backend.rag_pipeline.core.llm_providers import ModelNotFoundError
from backend.rag_pipeline.utils.logging import StructuredLogger
from backend.stt.service import get_stt_service
from backend.stt.transcriber import SUPPORTED_AUDIO_FORMATS

from .metrics import get_metrics

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/v1/qa", tags=["qa"])

# Initialize orchestrator
orchestrator = QueryOrchestrator()

VALID_STRATEGIES = ("dense", "sparse", "hybrid", "bm25")


class AskRequest(BaseModel):
    """Request payload for the ask endpoint."""

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
    """Response payload for the ask endpoint."""

    answer: str
    sources: list[dict]
    confidence: str
    chunks_retrieved: int
    average_similarity: float


class VoiceAskResponse(AskResponse):
    """Response for voice→query: RAG answer plus transcription metadata."""

    transcription_text: str = Field(..., description="Transcribed question text")
    transcription_language: str = Field(..., description="Detected language code (e.g. nl, en)")
    transcription_latency_ms: int = Field(..., description="Transcription duration in milliseconds")


@router.post("", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    """Ask a question about uploaded documents and get an answer with sources."""
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

        result = orchestrator.ask_question(
            question=payload.question,
            top_k=payload.top_k,
            similarity_threshold=payload.similarity_threshold,
            strategy=payload.strategy,
        )

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
        logger.warning("LLM model not available", model=e.model_name, host=e.host, error=str(e))
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


MAX_VOICE_AUDIO_SIZE = 50 * 1024 * 1024


@router.post("/voice", response_model=VoiceAskResponse)
async def ask_voice(audio: UploadFile = File(..., description="Audio file (e.g. WAV, MP3, WebM)")) -> VoiceAskResponse:
    """Voice query: transcribe audio, then run RAG question-answering."""
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

    t0 = time.perf_counter()
    try:
        stt_service = get_stt_service()
        transcription = stt_service.transcribe_only(
            audio_data=audio_data,
            file_extension=extension,
            language=None,
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

    try:
        get_metrics().record_query()
        llm_config = get_llm_config()
        logger.info(
            "Voice RAG flow: voice->text [transcribe]",
            question=question[:80],
            language=transcription.language,
            transcribe_ms=transcription_latency_ms,
        )

        result = orchestrator.ask_question(
            question=question,
            top_k=5,
            similarity_threshold=0.5,
            strategy="hybrid",
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
