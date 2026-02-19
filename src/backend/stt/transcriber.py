"""Speech-to-text transcription using faster-whisper.

This module provides on-premises transcription using the faster-whisper library,
which is a CTranslate2 implementation of OpenAI's Whisper model.

See docs/technical/CUDA_SETUP.md for GPU/CUDA configuration.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from backend.stt.models import TranscriptionResult

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

# Model configuration (env overrides at runtime)
DEFAULT_MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "small")


def _get_default_device() -> str:
    """Resolve device: explicit STT_DEVICE env, else auto-detect CUDA, else cpu."""
    explicit = os.getenv("STT_DEVICE")
    if explicit is not None and explicit.strip():
        return explicit.strip().lower()
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def _get_default_compute_type(device: str) -> str:
    """Resolve compute type: explicit STT_COMPUTE_TYPE env, else float16 for cuda, int8 for cpu."""
    explicit = os.getenv("STT_COMPUTE_TYPE")
    if explicit is not None and explicit.strip():
        return explicit.strip().lower()
    if device == "cuda":
        return "float16"
    return "int8"


class Transcriber:
    """Wrapper around faster-whisper for speech-to-text transcription."""

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ):
        """Initialize the transcriber.

        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large-v2", "large-v3",
                "turbo"). turbo = large-v3-turbo, good speed/accuracy for multilingual.
            device: Device for inference ("cpu" or "cuda"). If None, uses STT_DEVICE env or auto-detects
                CUDA when torch.cuda.is_available().
            compute_type: Computation type ("int8", "float16", "float32"). If None, uses STT_COMPUTE_TYPE
                env or float16 for cuda, int8 for cpu.
        """
        self.model_size = model_size or os.getenv("STT_MODEL_SIZE", "small")
        self.device = device if device is not None else _get_default_device()
        self.compute_type = compute_type if compute_type is not None else _get_default_compute_type(self.device)
        self._model = None

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the Whisper model on first use."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(f"Loading faster-whisper model: {self.model_size} on {self.device} ({self.compute_type})")
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                logger.info("Faster-whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load faster-whisper model: {e}")
                raise RuntimeError(f"Could not load STT model: {e}") from e

    def transcribe_file(
        self,
        file_path: str | Path,
        language: str | None = None,
        task: str = "transcribe",
    ) -> TranscriptionResult:
        """Transcribe an audio file.

        Args:
            file_path: Path to the audio file
            language: Language code (e.g., "nl", "en"). If None, auto-detect.
            task: "transcribe" or "translate" (translate to English)

        Returns:
            TranscriptionResult with text, confidence, and segments
        """
        self._ensure_model_loaded()

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        extension = file_path.suffix.lower()
        if extension not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio format: {extension}. Supported: {SUPPORTED_AUDIO_FORMATS}")

        logger.info(f"Transcribing audio file: {file_path}")

        try:
            segments, info = self._model.transcribe(
                str(file_path),
                language=language,
                task=task,
                beam_size=5,
                word_timestamps=False,
                vad_filter=True,  # Filter out silence
            )

            # Collect all segments
            segment_list = []
            all_text_parts = []
            total_confidence = 0.0
            segment_count = 0

            for segment in segments:
                segment_data = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "avg_logprob": segment.avg_logprob,
                    "no_speech_prob": segment.no_speech_prob,
                }
                segment_list.append(segment_data)
                all_text_parts.append(segment.text.strip())

                # Convert log probability to confidence (0-1 scale)
                # avg_logprob is typically between -1 and 0, where 0 is highest confidence
                segment_confidence = min(1.0, max(0.0, 1.0 + segment.avg_logprob))
                total_confidence += segment_confidence
                segment_count += 1

            full_text = " ".join(all_text_parts)
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0

            result = TranscriptionResult(
                text=full_text,
                language=info.language,
                confidence=round(avg_confidence, 3),
                duration_seconds=round(info.duration, 2),
                segments=segment_list,
            )

            logger.info(
                f"Transcription complete: {len(full_text)} chars, {segment_count} segments, confidence: {avg_confidence:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}") from e

    def transcribe_bytes(
        self,
        audio_data: bytes | BinaryIO,
        file_extension: str = ".wav",
        language: str | None = None,
        task: str = "transcribe",
    ) -> TranscriptionResult:
        """Transcribe audio from bytes or file-like object.

        Args:
            audio_data: Audio data as bytes or file-like object
            file_extension: File extension for temp file (e.g., ".wav", ".mp3")
            language: Language code (e.g., "nl", "en"). If None, auto-detect.
            task: "transcribe" or "translate" (translate to English)

        Returns:
            TranscriptionResult with text, confidence, and segments
        """
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as tmp_file:
            if isinstance(audio_data, bytes):
                tmp_file.write(audio_data)
            else:
                # File-like object
                tmp_file.write(audio_data.read())
            tmp_path = tmp_file.name

        try:
            return self.transcribe_file(tmp_path, language=language, task=task)
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "is_loaded": self._model is not None,
        }


# Global transcriber instance
_transcriber: Transcriber | None = None


def get_transcriber() -> Transcriber:
    """Get the global transcriber instance (lazy initialization)."""
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber()
    return _transcriber
