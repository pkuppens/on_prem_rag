"""Speech-to-Text API endpoints.

This module provides API endpoints for on-premises speech-to-text
transcription with context-aware LLM correction.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.stt.models import CorrectionConfig, STTResponse, UserRole
from backend.stt.service import get_stt_service
from backend.stt.transcriber import SUPPORTED_AUDIO_FORMATS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stt", tags=["Speech-to-Text"])

# Maximum audio file size (50 MB)
MAX_AUDIO_SIZE = 50 * 1024 * 1024

# Maximum audio duration (10 minutes)
MAX_AUDIO_DURATION = 600  # seconds


@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    role: str = Form(default="gp", description="User role (gp, patient, admin)"),
    language: str = Form(default="nl", description="Language code (e.g., nl, en)"),
    enable_correction: bool = Form(default=True, description="Enable context-aware correction"),
    conservative_mode: bool = Form(default=True, description="Use conservative (minimal) corrections"),
    conversation_context: str = Form(
        default="[]",
        description="JSON array of recent messages: [{'role': 'user', 'content': '...'}]",
    ),
    session_metadata: str = Form(
        default="{}",
        description="JSON object with session metadata",
    ),
) -> STTResponse:
    """Transcribe audio with optional context-aware correction.

    This endpoint accepts audio files, transcribes them using faster-whisper,
    and optionally applies context-aware LLM correction using the conversation
    history and medical glossary.

    The audio is processed entirely on-premises - no external API calls are made.

    Args:
        audio: Audio file (WAV, MP3, M4A, FLAC, OGG, WebM)
        role: User role for context (gp, patient, admin)
        language: Language code for transcription
        enable_correction: Whether to apply LLM correction
        conservative_mode: If True, apply minimal corrections
        conversation_context: JSON array of recent conversation messages
        session_metadata: JSON object with additional session context

    Returns:
        STTResponse with draft text, corrected text, and metadata
    """
    import json

    # Validate file type
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = Path(audio.filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {extension}. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}",
        )

    # Validate content type
    content_type = audio.content_type or ""
    if not content_type.startswith("audio/") and extension not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Expected audio/*",
        )

    # Read and validate file size
    audio_data = await audio.read()
    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Audio file too large: {len(audio_data) / 1024 / 1024:.1f} MB. Maximum: {MAX_AUDIO_SIZE / 1024 / 1024:.0f} MB",
        )

    # Parse role
    try:
        user_role = UserRole(role.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}. Must be one of: gp, patient, admin")

    # Parse conversation context
    try:
        context_list = json.loads(conversation_context)
        if not isinstance(context_list, list):
            context_list = []
    except json.JSONDecodeError:
        context_list = []

    # Parse session metadata
    try:
        metadata_dict = json.loads(session_metadata)
        if not isinstance(metadata_dict, dict):
            metadata_dict = {}
    except json.JSONDecodeError:
        metadata_dict = {}

    # Build correction config
    correction_config = CorrectionConfig(
        enabled=enable_correction,
        conservative_mode=conservative_mode,
        use_conversation_context=bool(context_list),
        use_glossary=True,
    )

    # Process with STT service
    try:
        stt_service = get_stt_service()
        result = stt_service.process_bytes(
            audio_data=audio_data,
            file_extension=extension,
            role=user_role,
            language=language if language else None,
            conversation_context=context_list,
            correction_config=correction_config,
            session_metadata=metadata_dict,
        )

        logger.info(
            f"STT complete: {len(result.draft_text)} chars, corrected={result.was_corrected}, time={result.processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.exception(f"STT processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/transcribe/draft")
async def transcribe_audio_draft(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form(default="nl", description="Language code (e.g., nl, en)"),
) -> dict[str, Any]:
    """Quick transcription without correction (draft mode).

    This endpoint provides fast transcription without the LLM correction step.
    Useful for getting a quick draft that the user can manually review.

    Args:
        audio: Audio file (WAV, MP3, M4A, FLAC, OGG, WebM)
        language: Language code for transcription

    Returns:
        Dict with text, confidence, and duration
    """
    # Validate file type
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = Path(audio.filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {extension}. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}",
        )

    # Read audio data
    audio_data = await audio.read()
    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Audio file too large: {len(audio_data) / 1024 / 1024:.1f} MB. Maximum: {MAX_AUDIO_SIZE / 1024 / 1024:.0f} MB",
        )

    try:
        stt_service = get_stt_service()
        result = stt_service.transcribe_only(
            audio_data=audio_data,
            file_extension=extension,
            language=language if language else None,
        )

        return {
            "text": result.text,
            "language": result.language,
            "confidence": result.confidence,
            "duration_seconds": result.duration_seconds,
        }

    except Exception as e:
        logger.exception(f"Draft transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.get("/health")
async def stt_health() -> dict[str, Any]:
    """Check health of STT service components.

    Returns:
        Dict with health status of transcriber and corrector
    """
    try:
        stt_service = get_stt_service()
        return stt_service.health_check()
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/info")
async def stt_info() -> dict[str, Any]:
    """Get information about STT service configuration.

    Returns:
        Dict with model and configuration information
    """
    try:
        stt_service = get_stt_service()
        return {
            "service": stt_service.get_service_info(),
            "supported_formats": list(SUPPORTED_AUDIO_FORMATS),
            "max_file_size_mb": MAX_AUDIO_SIZE / 1024 / 1024,
            "max_duration_seconds": MAX_AUDIO_DURATION,
        }
    except Exception as e:
        return {
            "error": str(e),
        }
