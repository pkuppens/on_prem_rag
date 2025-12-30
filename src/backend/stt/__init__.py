"""Speech-to-Text (STT) service with context-aware correction.

This module provides on-premises speech-to-text capabilities using faster-whisper,
with context-aware LLM correction for medical terminology and conversation coherence.
"""

from backend.stt.models import (
    CorrectionConfig,
    STTRequest,
    STTResponse,
    TranscriptionResult,
)
from backend.stt.service import STTService, get_stt_service

__all__ = [
    "STTService",
    "get_stt_service",
    "STTRequest",
    "STTResponse",
    "TranscriptionResult",
    "CorrectionConfig",
]
