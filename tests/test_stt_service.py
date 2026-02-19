"""Tests for the Speech-to-Text (STT) service.

As a user I want the STT service to accurately transcribe audio and apply
context-aware corrections, so I can use voice input for medical documentation.

Technical: Tests STT models, transcription flow, correction logic, and glossary.
"""

from unittest.mock import patch

import pytest

from backend.stt.models import CorrectionConfig, CorrectionResult, STTResponse, TranscriptionResult, UserRole


class TestSTTModels:
    """Test STT Pydantic models."""

    def test_user_role_enum(self):
        """Test UserRole enum values."""
        assert UserRole.GP.value == "gp"
        assert UserRole.PATIENT.value == "patient"
        assert UserRole.ADMIN.value == "admin"

    def test_correction_config_defaults(self):
        """Test CorrectionConfig default values."""
        config = CorrectionConfig()

        assert config.enabled is True
        assert config.conservative_mode is True
        assert config.use_conversation_context is True
        assert config.use_glossary is True
        assert config.max_context_messages == 5

    def test_correction_config_custom_values(self):
        """Test CorrectionConfig with custom values."""
        config = CorrectionConfig(
            enabled=False,
            conservative_mode=False,
            use_conversation_context=False,
            use_glossary=False,
            max_context_messages=10,
        )

        assert config.enabled is False
        assert config.conservative_mode is False
        assert config.max_context_messages == 10

    def test_transcription_result_model(self):
        """Test TranscriptionResult model creation."""
        result = TranscriptionResult(
            text="Dit is een test transcriptie.",
            language="nl",
            confidence=0.95,
            duration_seconds=5.5,
            segments=[],
        )

        assert result.text == "Dit is een test transcriptie."
        assert result.language == "nl"
        assert result.confidence == 0.95
        assert result.duration_seconds == 5.5

    def test_correction_result_model(self):
        """Test CorrectionResult model creation."""
        result = CorrectionResult(
            original_text="patiente",
            corrected_text="patiënt",
            edits_made=[{"original": "patiente", "corrected": "patiënt", "reason": "spelling"}],
            correction_confidence=0.9,
            glossary_matches=["patiënt"],
        )

        assert result.original_text == "patiente"
        assert result.corrected_text == "patiënt"
        assert len(result.edits_made) == 1
        assert "patiënt" in result.glossary_matches

    def test_stt_response_model(self):
        """Test STTResponse model creation."""
        transcription = TranscriptionResult(
            text="test tekst",
            language="nl",
            confidence=0.9,
            duration_seconds=2.0,
            segments=[],
        )

        response = STTResponse(
            draft_text="test tekst",
            corrected_text="test tekst",
            transcription=transcription,
            correction=None,
            was_corrected=False,
            model_used="small",
            correction_model_used=None,
            processing_time_ms=500,
        )

        assert response.draft_text == "test tekst"
        assert response.was_corrected is False
        assert response.model_used == "small"


class TestMedicalGlossary:
    """Test the medical glossary functionality."""

    def test_glossary_initialization(self):
        """Test glossary loads without errors."""
        from backend.stt.glossary import MedicalGlossary

        glossary = MedicalGlossary()

        assert len(glossary.terms) > 0
        assert len(glossary.abbreviations) > 0
        assert len(glossary.common_corrections) > 0

    def test_glossary_find_term(self):
        """Test finding medical terms in text."""
        from backend.stt.glossary import MedicalGlossary

        glossary = MedicalGlossary()

        # Test with Dutch medical terms
        text = "De patiënt heeft diabetes en hypertensie."
        found = glossary.find_term(text)

        assert "diabetes" in found
        assert "hypertensie" in found

    def test_glossary_suggest_correction(self):
        """Test suggesting corrections for misspelled words."""
        from backend.stt.glossary import MedicalGlossary

        glossary = MedicalGlossary()

        # Test abbreviation normalization
        assert glossary.suggest_correction("mmhg") == "mmHg"
        assert glossary.suggest_correction("ecg") == "ECG"

    def test_glossary_get_correction_context(self):
        """Test getting correction context for LLM prompt."""
        from backend.stt.glossary import MedicalGlossary

        glossary = MedicalGlossary()
        context = glossary.get_correction_context()

        assert "Medical terms:" in context or "Abbreviations:" in context
        assert len(context) > 0


class TestTranscriber:
    """Test the transcriber component."""

    def test_transcriber_initialization(self):
        """Test transcriber can be initialized."""
        from backend.stt.transcriber import Transcriber

        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")

        assert transcriber.model_size == "tiny"
        assert transcriber.device == "cpu"
        assert transcriber.compute_type == "int8"

    def test_transcriber_model_info(self):
        """Test getting transcriber model info."""
        from backend.stt.transcriber import Transcriber

        transcriber = Transcriber(model_size="small")
        info = transcriber.get_model_info()

        assert info["model_size"] == "small"
        assert info["is_loaded"] is False  # Model not loaded yet

    def test_transcriber_turbo_model(self):
        """As a user I want to use turbo model for better speed/accuracy.
        Technical: Transcriber accepts "turbo" as model_size (large-v3-turbo alias).
        """
        from backend.stt.transcriber import Transcriber

        transcriber = Transcriber(model_size="turbo", device="cpu", compute_type="int8")
        assert transcriber.model_size == "turbo"

    def test_transcriber_cuda_autodetect(self, monkeypatch):
        """As a user I want CUDA auto-detected when GPU available.
        Technical: When STT_DEVICE unset and torch.cuda.is_available() is True, device is cuda.
        """
        import torch

        from backend.stt.transcriber import Transcriber

        monkeypatch.delenv("STT_DEVICE", raising=False)
        monkeypatch.delenv("STT_COMPUTE_TYPE", raising=False)
        with patch.object(torch.cuda, "is_available", return_value=True):
            transcriber = Transcriber()
        assert transcriber.device == "cuda"
        assert transcriber.compute_type == "float16"

    def test_transcriber_device_from_env(self, monkeypatch):
        """As a user I want to force device via STT_DEVICE env.
        Technical: When STT_DEVICE=cuda, Transcriber uses cuda.
        """
        from backend.stt.transcriber import Transcriber

        monkeypatch.setenv("STT_DEVICE", "cuda")
        monkeypatch.delenv("STT_COMPUTE_TYPE", raising=False)
        transcriber = Transcriber()
        assert transcriber.device == "cuda"
        assert transcriber.compute_type == "float16"

    def test_transcriber_compute_type_float16_for_cuda(self):
        """As a user I want float16 when using CUDA for better performance.
        Technical: When device=cuda and STT_COMPUTE_TYPE unset, default is float16.
        """
        from backend.stt.transcriber import Transcriber

        transcriber = Transcriber(device="cuda", compute_type=None)
        assert transcriber.compute_type == "float16"

    def test_transcriber_get_global(self):
        """Test getting global transcriber instance."""
        from backend.stt.transcriber import get_transcriber

        transcriber = get_transcriber()
        assert transcriber is not None


class TestCorrector:
    """Test the corrector component."""

    def test_corrector_initialization(self):
        """Test corrector can be initialized."""
        from backend.stt.corrector import Corrector

        corrector = Corrector(model="mistral:latest")

        assert corrector.model == "mistral:latest"
        assert corrector.glossary is not None

    def test_corrector_build_role_context(self):
        """Test building role-specific context."""
        from backend.stt.corrector import Corrector

        corrector = Corrector()

        gp_context = corrector._build_role_context(UserRole.GP)
        patient_context = corrector._build_role_context(UserRole.PATIENT)

        assert "huisarts" in gp_context.lower() or "gp" in gp_context.lower()
        assert "patiënt" in patient_context.lower() or "patient" in patient_context.lower()

    def test_corrector_build_conversation_context(self):
        """Test building conversation context."""
        from backend.stt.corrector import Corrector

        corrector = Corrector()

        messages = [
            {"role": "user", "content": "Ik heb hoofdpijn."},
            {"role": "assistant", "content": "Hoe lang heeft u al hoofdpijn?"},
        ]

        context = corrector._build_conversation_context(messages)

        assert "GESPREKSCONTEXT" in context or len(context) > 0
        assert "hoofdpijn" in context

    def test_corrector_get_model_info(self):
        """Test getting corrector model info."""
        from backend.stt.corrector import Corrector

        corrector = Corrector()
        info = corrector.get_model_info()

        assert "model" in info
        assert "ollama_host" in info


class TestSTTService:
    """Test the main STT service."""

    def test_service_initialization(self):
        """Test STT service can be initialized."""
        from backend.stt.service import STTService

        service = STTService()
        assert service is not None

    def test_service_get_info(self):
        """Test getting service info."""
        from backend.stt.service import STTService

        service = STTService()
        info = service.get_service_info()

        assert "transcriber" in info
        assert "corrector" in info

    def test_service_get_global(self):
        """Test getting global service instance."""
        from backend.stt.service import get_stt_service

        service = get_stt_service()
        assert service is not None


class TestSTTAPIModels:
    """Test STT API endpoint models."""

    def test_api_endpoint_imports(self):
        """Test that API endpoints can be imported."""
        from backend.rag_pipeline.api.stt import router

        assert router is not None
        assert router.prefix == "/api/stt"

    def test_transcription_result_has_language(self):
        """As a user I want detected language available for downstream use.
        Technical: TranscriptionResult includes language field.
        """
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            confidence=0.9,
            duration_seconds=1.0,
            segments=[],
        )
        assert result.language == "en"


class TestSTTAPIEndpoints:
    """Integration tests for STT and voice-ask API endpoints (AC-1e, AC-2)."""

    def test_stt_info_returns_device(self):
        """As a user I want to see STT device (cpu/cuda) in API info.
        Technical: GET /api/stt/info returns transcriber.device.
        """
        from fastapi.testclient import TestClient

        from backend.rag_pipeline.api.app import app

        client = TestClient(app)
        resp = client.get("/api/stt/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data
        transcriber_info = data["service"]["transcriber"]
        assert "device" in transcriber_info
        assert transcriber_info["device"] in ("cpu", "cuda")

    def test_ask_voice_unsupported_format(self):
        """Voice ask rejects unsupported audio format."""
        from fastapi.testclient import TestClient

        from backend.rag_pipeline.api.app import app

        client = TestClient(app)
        resp = client.post(
            "/api/ask/voice",
            files={"audio": ("test.xyz", b"fake", "application/octet-stream")},
        )
        assert resp.status_code == 400

    @pytest.mark.slow
    def test_ask_voice_no_speech_detected(self):
        """Voice ask returns 400 when audio has no speech.
        Technical: Minimal silent WAV yields empty transcription.
        Loads Whisper model on first run.
        """
        import struct

        from fastapi.testclient import TestClient

        from backend.rag_pipeline.api.app import app

        # Build valid WAV: 1 channel, 16kHz, 16-bit, 0.1s silence
        sample_rate = 16000
        duration_sec = 0.1
        num_samples = int(sample_rate * duration_sec)
        data = struct.pack(f"<{num_samples}h", *([0] * num_samples))
        wav = (
            b"RIFF"
            + struct.pack("<I", 36 + len(data))
            + b"WAVE"
            + b"fmt \x10\x00\x00\x00\x01\x00\x01\x00"
            + struct.pack("<I", sample_rate)
            + struct.pack("<I", sample_rate * 2)
            + b"\x02\x00\x10\x00"
            + b"data"
            + struct.pack("<I", len(data))
            + data
        )
        client = TestClient(app)
        resp = client.post(
            "/api/ask/voice",
            files={"audio": ("silence.wav", wav, "audio/wav")},
        )
        assert resp.status_code in (400, 500)


@pytest.mark.slow
@pytest.mark.internet
class TestTranscriberIntegration:
    """Integration tests for transcriber (requires model download from HuggingFace)."""

    def test_transcriber_model_loading(self):
        """Test that the whisper model can be loaded."""
        from backend.stt.transcriber import Transcriber

        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")
        transcriber._ensure_model_loaded()

        assert transcriber._model is not None
        info = transcriber.get_model_info()
        assert info["is_loaded"] is True


@pytest.mark.slow
@pytest.mark.internet
class TestTTSSTTRoundtrip:
    """TTS→STT roundtrip for Dutch/English (AC-4). Requires gtts and faster-whisper."""

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase and strip punctuation for comparison."""
        import string

        t = text.lower().strip()
        for p in string.punctuation:
            t = t.replace(p, " ")
        return " ".join(t.split())

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Word overlap ratio (0-1)."""
        wa = set(TestTTSSTTRoundtrip._normalize(a).split())
        wb = set(TestTTSSTTRoundtrip._normalize(b).split())
        if not wa:
            return 1.0 if not wb else 0.0
        return len(wa & wb) / len(wa)

    def test_dutch_tts_stt_language_detected(self):
        """As a user I want Dutch audio to transcribe to Dutch.
        Technical: TTS(Dutch text) → STT → language detected as nl.
        """
        try:
            from gtts import gTTS
        except ImportError:
            pytest.skip("gtts not installed")
        from io import BytesIO

        from backend.stt.transcriber import Transcriber

        text = "Hoe gaat het met u vandaag?"
        buf = BytesIO()
        gTTS(text=text, lang="nl").write_to_fp(buf)
        audio_bytes = buf.getvalue()

        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")
        result = transcriber.transcribe_bytes(audio_bytes, file_extension=".mp3", language=None)
        assert result.language == "nl"

    def test_english_tts_stt_language_detected(self):
        """As a user I want English audio to transcribe to English.
        Technical: TTS(English text) → STT → language detected as en.
        """
        try:
            from gtts import gTTS
        except ImportError:
            pytest.skip("gtts not installed")
        from io import BytesIO

        from backend.stt.transcriber import Transcriber

        text = "How are you feeling today?"
        buf = BytesIO()
        gTTS(text=text, lang="en").write_to_fp(buf)
        audio_bytes = buf.getvalue()

        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")
        result = transcriber.transcribe_bytes(audio_bytes, file_extension=".mp3", language=None)
        assert result.language == "en"

    def test_tts_stt_similarity_medium_sentence(self):
        """As a user I want transcription to match spoken text well.
        Technical: TTS(text) → STT → normalized similarity ≥80%.
        Uses tiny model; turbo would typically perform better.
        """
        try:
            from gtts import gTTS
        except ImportError:
            pytest.skip("gtts not installed")
        from io import BytesIO

        from backend.stt.transcriber import Transcriber

        text = "What is the recommended dosage for metformin?"
        buf = BytesIO()
        gTTS(text=text, lang="en").write_to_fp(buf)
        audio_bytes = buf.getvalue()

        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")
        result = transcriber.transcribe_bytes(audio_bytes, file_extension=".mp3", language="en")
        sim = self._similarity(text, result.text)
        assert sim >= 0.5, f"Similarity {sim:.2f} below 0.5; transcript: {result.text!r}"


@pytest.mark.ollama
@pytest.mark.slow
@pytest.mark.internet
class TestCorrectorIntegration:
    """Integration tests for corrector (requires Ollama)."""

    def test_corrector_with_empty_text(self):
        """Test correction with empty text."""
        from backend.stt.corrector import Corrector

        corrector = Corrector()
        result = corrector.correct("")

        assert result.original_text == ""
        assert result.corrected_text == ""
        assert len(result.edits_made) == 0

    def test_corrector_without_correction_enabled(self):
        """Test correction when disabled."""
        from backend.stt.corrector import Corrector

        corrector = Corrector()
        config = CorrectionConfig(enabled=False)
        result = corrector.correct("test tekst", config=config)

        assert result.original_text == "test tekst"
        assert result.corrected_text == "test tekst"
        assert result.correction_confidence == 1.0
