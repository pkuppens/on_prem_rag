"""Main STT service combining transcription and correction.

This module provides the unified interface for speech-to-text processing,
combining faster-whisper transcription with context-aware LLM correction.
"""

import logging
import time
from pathlib import Path
from typing import Any, BinaryIO

from backend.stt.corrector import Corrector, get_corrector
from backend.stt.models import CorrectionConfig, STTResponse, TranscriptionResult, UserRole
from backend.stt.transcriber import Transcriber, get_transcriber

logger = logging.getLogger(__name__)


class STTService:
    """Unified speech-to-text service with context-aware correction."""

    def __init__(
        self,
        transcriber: Transcriber | None = None,
        corrector: Corrector | None = None,
    ):
        """Initialize the STT service.

        Args:
            transcriber: Transcriber instance (uses global if not provided)
            corrector: Corrector instance (uses global if not provided)
        """
        self._transcriber = transcriber
        self._corrector = corrector

    @property
    def transcriber(self) -> Transcriber:
        """Get the transcriber instance (lazy initialization)."""
        if self._transcriber is None:
            self._transcriber = get_transcriber()
        return self._transcriber

    @property
    def corrector(self) -> Corrector:
        """Get the corrector instance (lazy initialization)."""
        if self._corrector is None:
            self._corrector = get_corrector()
        return self._corrector

    def process_file(
        self,
        file_path: str | Path,
        role: UserRole = UserRole.GP,
        language: str | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        correction_config: CorrectionConfig | None = None,
        session_metadata: dict[str, Any] | None = None,
    ) -> STTResponse:
        """Process an audio file through transcription and correction.

        Args:
            file_path: Path to the audio file
            role: User role for context-aware correction
            language: Language code (e.g., "nl", "en"). If None, auto-detect.
            conversation_context: Recent conversation messages for context
            correction_config: Configuration for correction behavior
            session_metadata: Additional session metadata

        Returns:
            STTResponse with transcription and correction results
        """
        start_time = time.perf_counter()

        # Step 1: Transcribe
        logger.info(f"Processing audio file: {file_path}")
        transcription = self.transcriber.transcribe_file(file_path, language=language)

        # Step 2: Correct (if enabled)
        correction_config = correction_config or CorrectionConfig()
        correction = None
        corrected_text = transcription.text
        was_corrected = False

        if correction_config.enabled and transcription.text.strip():
            correction = self.corrector.correct(
                text=transcription.text,
                role=role,
                conversation_context=conversation_context,
                config=correction_config,
                session_metadata=session_metadata,
            )
            corrected_text = correction.corrected_text
            was_corrected = corrected_text != transcription.text

        # Calculate processing time
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return STTResponse(
            draft_text=transcription.text,
            corrected_text=corrected_text,
            transcription=transcription,
            correction=correction,
            was_corrected=was_corrected,
            model_used=self.transcriber.model_size,
            correction_model_used=self.corrector.model if correction_config.enabled else None,
            processing_time_ms=processing_time_ms,
        )

    def process_bytes(
        self,
        audio_data: bytes | BinaryIO,
        file_extension: str = ".wav",
        role: UserRole = UserRole.GP,
        language: str | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        correction_config: CorrectionConfig | None = None,
        session_metadata: dict[str, Any] | None = None,
    ) -> STTResponse:
        """Process audio bytes through transcription and correction.

        Args:
            audio_data: Audio data as bytes or file-like object
            file_extension: File extension (e.g., ".wav", ".mp3")
            role: User role for context-aware correction
            language: Language code (e.g., "nl", "en"). If None, auto-detect.
            conversation_context: Recent conversation messages for context
            correction_config: Configuration for correction behavior
            session_metadata: Additional session metadata

        Returns:
            STTResponse with transcription and correction results
        """
        start_time = time.perf_counter()

        # Step 1: Transcribe
        logger.info(f"Processing audio bytes ({file_extension})")
        transcription = self.transcriber.transcribe_bytes(
            audio_data,
            file_extension=file_extension,
            language=language,
        )

        # Step 2: Correct (if enabled)
        correction_config = correction_config or CorrectionConfig()
        correction = None
        corrected_text = transcription.text
        was_corrected = False

        if correction_config.enabled and transcription.text.strip():
            correction = self.corrector.correct(
                text=transcription.text,
                role=role,
                conversation_context=conversation_context,
                config=correction_config,
                session_metadata=session_metadata,
            )
            corrected_text = correction.corrected_text
            was_corrected = corrected_text != transcription.text

        # Calculate processing time
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return STTResponse(
            draft_text=transcription.text,
            corrected_text=corrected_text,
            transcription=transcription,
            correction=correction,
            was_corrected=was_corrected,
            model_used=self.transcriber.model_size,
            correction_model_used=self.corrector.model if correction_config.enabled else None,
            processing_time_ms=processing_time_ms,
        )

    def transcribe_only(
        self,
        file_path: str | Path | None = None,
        audio_data: bytes | BinaryIO | None = None,
        file_extension: str = ".wav",
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio without correction (for quick drafts).

        Either file_path or audio_data must be provided.

        Args:
            file_path: Path to the audio file
            audio_data: Audio data as bytes or file-like object
            file_extension: File extension (if using audio_data)
            language: Language code (e.g., "nl", "en"). If None, auto-detect.

        Returns:
            TranscriptionResult with raw transcription
        """
        if file_path:
            return self.transcriber.transcribe_file(file_path, language=language)
        elif audio_data:
            return self.transcriber.transcribe_bytes(audio_data, file_extension, language=language)
        else:
            raise ValueError("Either file_path or audio_data must be provided")

    def get_service_info(self) -> dict:
        """Get information about the STT service configuration."""
        return {
            "transcriber": self.transcriber.get_model_info(),
            "corrector": self.corrector.get_model_info(),
        }

    def health_check(self) -> dict:
        """Check health of STT service components."""
        health = {
            "transcriber": {
                "status": "unknown",
                "model": self.transcriber.model_size,
            },
            "corrector": {
                "status": "unknown",
                "model": self.corrector.model,
            },
        }

        # Check transcriber (just verify model can be loaded)
        try:
            self.transcriber._ensure_model_loaded()
            health["transcriber"]["status"] = "healthy"
        except Exception as e:
            health["transcriber"]["status"] = "unhealthy"
            health["transcriber"]["error"] = str(e)

        # Check corrector (verify Ollama connection)
        try:
            self.corrector._ensure_client()
            health["corrector"]["status"] = "healthy"
        except Exception as e:
            health["corrector"]["status"] = "unhealthy"
            health["corrector"]["error"] = str(e)

        return health


# Global STT service instance
_stt_service: STTService | None = None


def get_stt_service() -> STTService:
    """Get the global STT service instance (lazy initialization)."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
