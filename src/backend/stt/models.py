"""Pydantic models for STT service requests and responses."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role for context-aware correction."""

    GP = "gp"
    PATIENT = "patient"
    ADMIN = "admin"


class CorrectionConfig(BaseModel):
    """Configuration for context-aware correction."""

    enabled: bool = Field(default=True, description="Whether to apply LLM correction")
    conservative_mode: bool = Field(
        default=True,
        description="If True, apply minimal edits. If False, allow more aggressive corrections.",
    )
    use_conversation_context: bool = Field(
        default=True,
        description="Whether to use recent conversation history for context",
    )
    use_glossary: bool = Field(
        default=True,
        description="Whether to use the medical glossary for corrections",
    )
    max_context_messages: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Maximum number of recent messages to include as context",
    )


class STTRequest(BaseModel):
    """Request model for STT transcription."""

    # Audio data is sent as file upload, not in JSON
    role: UserRole = Field(default=UserRole.GP, description="User role for context-aware correction")
    language: str = Field(default="nl", description="Language code (e.g., 'nl', 'en')")
    conversation_context: list[dict[str, str]] = Field(
        default_factory=list,
        description="Recent conversation messages for context. Format: [{'role': 'user/assistant', 'content': '...'}]",
    )
    correction_config: CorrectionConfig = Field(
        default_factory=CorrectionConfig,
        description="Configuration for context-aware correction",
    )
    session_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata (patient name, etc.) for context",
    )


class TranscriptionResult(BaseModel):
    """Result of the raw transcription step."""

    text: str = Field(description="Raw transcribed text from audio")
    language: str = Field(description="Detected or specified language")
    confidence: float = Field(ge=0.0, le=1.0, description="Average confidence score (0-1)")
    duration_seconds: float = Field(ge=0.0, description="Duration of audio in seconds")
    segments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed segments with timestamps and per-segment confidence",
    )


class CorrectionResult(BaseModel):
    """Result of the correction step."""

    original_text: str = Field(description="Original transcribed text before correction")
    corrected_text: str = Field(description="Text after context-aware correction")
    edits_made: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of edits made. Format: [{'original': '...', 'corrected': '...', 'reason': '...'}]",
    )
    correction_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the corrections (0-1)")
    glossary_matches: list[str] = Field(
        default_factory=list,
        description="Medical terms from glossary that were recognized/corrected",
    )


class STTResponse(BaseModel):
    """Full response from STT service including transcription and correction."""

    draft_text: str = Field(description="Raw transcribed text before correction")
    corrected_text: str = Field(description="Final text after context-aware correction")
    transcription: TranscriptionResult = Field(description="Detailed transcription results")
    correction: CorrectionResult | None = Field(
        default=None,
        description="Correction details (None if correction was disabled)",
    )
    was_corrected: bool = Field(description="Whether any corrections were made")
    model_used: str = Field(description="Whisper model used for transcription")
    correction_model_used: str | None = Field(
        default=None,
        description="LLM model used for correction (if applied)",
    )
    processing_time_ms: int = Field(ge=0, description="Total processing time in milliseconds")
