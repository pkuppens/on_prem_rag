"""Audio handling for Chainlit UI with on-prem STT.

This module provides audio recording and transcription integration
for the Chainlit chat interface, using the backend STT service.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import chainlit as cl
import httpx

from frontend.chat.utils.session import SessionManager, UserRole

logger = logging.getLogger(__name__)

# STT service configuration
STT_BACKEND_URL = os.getenv("STT_BACKEND_URL", "http://localhost:8000/api/stt")

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
SUPPORTED_MIME_TYPES = {
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/flac": ".flac",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
}

# Maximum audio file size (50 MB)
MAX_AUDIO_SIZE = 50 * 1024 * 1024


class AudioHandler:
    """Handles audio recording and transcription for Chainlit UI."""

    def __init__(self):
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for STT backend."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=120.0)  # 2 minute timeout for transcription
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def _validate_audio_file(self, element: Any) -> str | None:
        """Validate an audio file element.

        Returns None if valid, or an error message if invalid.
        """
        file_name = getattr(element, "name", None)
        if not file_name:
            return "Audio file has no name"

        extension = Path(file_name).suffix.lower()
        if extension not in SUPPORTED_AUDIO_FORMATS:
            return f"Unsupported audio format '{extension}'. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"

        # Check file size if path is available
        file_path = getattr(element, "path", None)
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > MAX_AUDIO_SIZE:
                return f"Audio file too large ({file_size / 1024 / 1024:.1f} MB). Maximum: {MAX_AUDIO_SIZE / 1024 / 1024:.0f} MB"

        return None

    def _get_conversation_context(self, max_messages: int = 5) -> list[dict[str, str]]:
        """Get recent conversation history for context."""
        session = SessionManager.get_session()
        if not session:
            return []

        history = session.conversation_history[-max_messages:]
        return [{"role": msg["role"], "content": msg["content"][:500]} for msg in history]

    async def process_audio(
        self,
        element: Any,
        enable_correction: bool = True,
        conservative_mode: bool = True,
    ) -> dict[str, Any]:
        """Process an audio file through the STT service.

        Args:
            element: Chainlit file element with audio data
            enable_correction: Whether to enable LLM correction
            conservative_mode: Use conservative (minimal) corrections

        Returns:
            Dict with transcription results
        """
        session = SessionManager.get_session()
        role = session.role if session else UserRole.GP

        file_name = getattr(element, "name", "audio.wav")
        file_path = getattr(element, "path", None)

        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"Audio file path not found: {file_path}")

        extension = Path(file_name).suffix.lower()

        # Read audio data
        with open(file_path, "rb") as f:
            audio_data = f.read()

        # Prepare request
        client = await self._get_client()
        conversation_context = self._get_conversation_context()

        files = {"audio": (file_name, audio_data, f"audio/{extension.lstrip('.')}")}
        data = {
            "role": role.value,
            "language": "nl",  # Default to Dutch
            "enable_correction": str(enable_correction).lower(),
            "conservative_mode": str(conservative_mode).lower(),
            "conversation_context": json.dumps(conversation_context),
            "session_metadata": json.dumps({"source": "chainlit_audio"}),
        }

        logger.info(f"Sending audio to STT service: {file_name} ({len(audio_data)} bytes)")

        try:
            response = await client.post(f"{STT_BACKEND_URL}/transcribe", files=files, data=data)
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"STT result: {len(result.get('corrected_text', ''))} chars, corrected={result.get('was_corrected', False)}"
            )

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"STT service error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Transcription failed: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"STT service connection error: {e}")
            raise RuntimeError(f"Could not connect to STT service: {e}") from e

    async def handle_audio_upload(self, element: Any) -> str | None:
        """Handle an uploaded audio file and return transcribed text.

        Args:
            element: Chainlit file element with audio data

        Returns:
            Transcribed and corrected text, or None on failure
        """
        # Validate
        validation_error = self._validate_audio_file(element)
        if validation_error:
            await cl.Message(content=f"Cannot process audio: {validation_error}").send()
            return None

        file_name = getattr(element, "name", "audio")

        # Show processing indicator
        async with cl.Step(name="Voice Transcription", type="run") as step:
            step.input = f"Processing: {file_name}"

            try:
                # Process through STT service
                result = await self.process_audio(element)

                draft_text = result.get("draft_text", "")
                corrected_text = result.get("corrected_text", draft_text)
                was_corrected = result.get("was_corrected", False)
                processing_time = result.get("processing_time_ms", 0)

                # Show results with indicators
                if was_corrected:
                    correction_info = result.get("correction", {})
                    edits = correction_info.get("edits_made", [])
                    edit_count = len(edits)

                    step.output = (
                        f"Transcribed and corrected ({edit_count} corrections)\n\n"
                        f"**Original:** {draft_text}\n\n"
                        f"**Corrected:** {corrected_text}"
                    )

                    # Show correction details if any
                    if edits:
                        corrections_text = "\n".join([f"- '{e.get('original')}' → '{e.get('corrected')}'" for e in edits[:5]])
                        await cl.Message(
                            content=f"**Corrections made:**\n{corrections_text}",
                            author="STT",
                        ).send()
                else:
                    step.output = f"Transcribed ({processing_time}ms): {corrected_text}"

                return corrected_text

            except Exception as e:
                step.output = f"Transcription failed: {e}"
                logger.exception(f"Audio transcription failed: {e}")
                await cl.Message(content=f"Could not transcribe audio: {e}").send()
                return None

    async def create_transcription_message(
        self,
        text: str,
        was_corrected: bool = False,
        edits: list[dict[str, str]] | None = None,
    ) -> cl.Message:
        """Create a message with transcription indicators.

        Args:
            text: Transcribed text
            was_corrected: Whether corrections were applied
            edits: List of corrections made

        Returns:
            Chainlit Message with appropriate formatting
        """
        # Build message with indicators
        if was_corrected and edits:
            # Show that text was transcribed and corrected
            header = "**Transcribed & Corrected**"
            correction_note = f"({len(edits)} correction{'s' if len(edits) > 1 else ''} applied)"
            content = f"{header} {correction_note}\n\n{text}"
        elif was_corrected:
            header = "**Transcribed & Corrected**"
            content = f"{header}\n\n{text}"
        else:
            header = "**Transcribed**"
            content = f"{header}\n\n{text}"

        return cl.Message(content=content, author="Voice Input")


# Global audio handler instance
_audio_handler: AudioHandler | None = None


def get_audio_handler() -> AudioHandler:
    """Get the global audio handler instance."""
    global _audio_handler
    if _audio_handler is None:
        _audio_handler = AudioHandler()
    return _audio_handler


def is_audio_file(element: Any) -> bool:
    """Check if a Chainlit element is an audio file."""
    file_name = getattr(element, "name", "")
    if not file_name:
        return False

    extension = Path(file_name).suffix.lower()
    if extension in SUPPORTED_AUDIO_FORMATS:
        return True

    # Check MIME type
    mime_type = getattr(element, "mime", "")
    return mime_type in SUPPORTED_MIME_TYPES
