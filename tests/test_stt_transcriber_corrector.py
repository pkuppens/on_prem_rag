# tests/test_stt_transcriber_corrector.py
"""Tests for the speech-to-text Transcriber and Corrector behaviour.

As a GP I want dictated audio transcribed and cleaned up reliably,
so that I get usable text, and clear errors when something is wrong.
Technical: faster-whisper and Ollama are replaced by fakes so no model or server is needed.
"""

import io
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.stt import transcriber as transcriber_module
from backend.stt.corrector import Corrector
from backend.stt.models import CorrectionConfig, UserRole
from backend.stt.transcriber import Transcriber


def fake_segment(id_, text, avg_logprob=-0.2):
    return SimpleNamespace(id=id_, start=float(id_), end=id_ + 1.0, text=text, avg_logprob=avg_logprob, no_speech_prob=0.01)


@pytest.fixture
def audio_file(tmp_path):
    path = tmp_path / "dictation.wav"
    path.write_bytes(b"RIFF")
    return path


@pytest.fixture
def loaded_transcriber():
    """A Transcriber with a fake model already injected (skips lazy loading)."""
    transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")
    transcriber._model = MagicMock()
    return transcriber


class TestDeviceResolution:
    def test_explicit_env_device_is_lowercased(self, monkeypatch):
        """STT_DEVICE wins over auto-detection and is normalised."""
        monkeypatch.setenv("STT_DEVICE", " CUDA ")

        assert transcriber_module._get_default_device() == "cuda"

    def test_falls_back_to_cpu_when_torch_is_missing(self, monkeypatch):
        """Without env override and without torch the device is cpu."""
        monkeypatch.delenv("STT_DEVICE", raising=False)
        monkeypatch.setitem(sys.modules, "torch", None)

        assert transcriber_module._get_default_device() == "cpu"

    @pytest.mark.parametrize(
        ("env", "device", "expected"),
        [("BFLOAT16", "cpu", "bfloat16"), (None, "cuda", "float16"), (None, "cpu", "int8")],
        ids=["env-override", "cuda-default", "cpu-default"],
    )
    def test_compute_type_resolution(self, monkeypatch, env, device, expected):
        """Compute type: env override first, then float16 for cuda, int8 for cpu."""
        if env is None:
            monkeypatch.delenv("STT_COMPUTE_TYPE", raising=False)
        else:
            monkeypatch.setenv("STT_COMPUTE_TYPE", env)

        assert transcriber_module._get_default_compute_type(device) == expected


class TestModelLoading:
    def test_model_is_loaded_lazily_once(self, monkeypatch):
        """The Whisper model is created on first use and reused afterwards."""
        whisper = MagicMock()
        monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=whisper))
        transcriber = Transcriber(model_size="tiny", device="cpu", compute_type="int8")

        transcriber._ensure_model_loaded()
        transcriber._ensure_model_loaded()

        whisper.assert_called_once_with("tiny", device="cpu", compute_type="int8")
        assert transcriber.get_model_info()["is_loaded"] is True

    def test_load_failure_is_wrapped_in_runtime_error(self, monkeypatch):
        """A failing model load surfaces as RuntimeError with a readable message."""
        whisper = MagicMock(side_effect=OSError("no weights"))
        monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=whisper))

        with pytest.raises(RuntimeError, match="Could not load STT model: no weights"):
            Transcriber(device="cpu", compute_type="int8")._ensure_model_loaded()


class TestTranscribeFile:
    def test_missing_file_raises_file_not_found(self, loaded_transcriber, tmp_path):
        """A non-existent path is rejected before the model is used."""
        with pytest.raises(FileNotFoundError):
            loaded_transcriber.transcribe_file(tmp_path / "nope.wav")

    def test_unsupported_extension_raises_value_error(self, loaded_transcriber, tmp_path):
        """Only the supported audio formats are accepted."""
        bad = tmp_path / "notes.txt"
        bad.write_text("hello")

        with pytest.raises(ValueError, match="Unsupported audio format"):
            loaded_transcriber.transcribe_file(bad)

    def test_segments_are_joined_and_confidence_averaged(self, loaded_transcriber, audio_file):
        """Text is the stripped segments joined by a space; confidence is 1+avg_logprob averaged, clamped to 0..1."""
        segments = [fake_segment(0, " Hello ", -0.2), fake_segment(1, "world", -5.0)]
        loaded_transcriber._model.transcribe.return_value = (iter(segments), SimpleNamespace(language="en", duration=3.456))

        result = loaded_transcriber.transcribe_file(audio_file, language="en")

        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.duration_seconds == 3.46
        assert result.confidence == 0.4  # (0.8 + 0.0) / 2
        assert [s["text"] for s in result.segments] == ["Hello", "world"]

    def test_no_speech_gives_empty_text_and_zero_confidence(self, loaded_transcriber, audio_file):
        """Silence yields an empty transcript instead of a division error."""
        loaded_transcriber._model.transcribe.return_value = (iter([]), SimpleNamespace(language="nl", duration=1.0))

        result = loaded_transcriber.transcribe_file(audio_file)

        assert result.text == ""
        assert result.confidence == 0.0

    def test_model_error_is_wrapped_in_runtime_error(self, loaded_transcriber, audio_file):
        """Failures inside the model are reported as RuntimeError('Transcription failed: ...')."""
        loaded_transcriber._model.transcribe.side_effect = ValueError("corrupt audio")

        with pytest.raises(RuntimeError, match="Transcription failed: corrupt audio"):
            loaded_transcriber.transcribe_file(audio_file)


class TestTranscribeBytes:
    @pytest.mark.parametrize("as_stream", [False, True], ids=["bytes", "file-like"])
    def test_temp_file_is_transcribed_and_removed(self, loaded_transcriber, tmp_path, as_stream):
        """Bytes and file-like input are written to a temp file with the right extension, then cleaned up."""
        seen = {}

        def fake_transcribe(path, language=None, task="transcribe"):
            seen["path"] = path
            seen["exists"] = os.path.exists(path)
            return "RESULT"

        loaded_transcriber.transcribe_file = fake_transcribe
        data = io.BytesIO(b"abc") if as_stream else b"abc"

        result = loaded_transcriber.transcribe_bytes(data, file_extension=".mp3")

        assert result == "RESULT"
        assert seen["path"].endswith(".mp3")
        assert seen["exists"] is True
        assert not os.path.exists(seen["path"])


def test_get_transcriber_returns_same_instance(monkeypatch):
    """The global accessor lazily creates a single shared Transcriber."""
    monkeypatch.setattr(transcriber_module, "_transcriber", None)

    assert transcriber_module.get_transcriber() is transcriber_module.get_transcriber()


class TestCorrectorParsing:
    @pytest.fixture
    def corrector(self):
        return Corrector(model="test-model")

    def test_json_inside_chatter_is_extracted(self, corrector):
        """JSON embedded in extra LLM prose is still parsed."""
        response = 'Sure! {"corrected_text": "fixed", "edits": [{"from": "a", "to": "b"}], "confidence": 0.9} Done.'

        text, edits, confidence = corrector._parse_llm_response(response, "original")

        assert (text, confidence) == ("fixed", 0.9)
        assert edits == [{"from": "a", "to": "b"}]

    @pytest.mark.parametrize("response", ["no json at all", "{broken json}"], ids=["no-json", "invalid-json"])
    def test_unparseable_response_falls_back_to_original(self, corrector, response):
        """If the LLM output cannot be parsed, the original text is kept with low confidence."""
        assert corrector._parse_llm_response(response, "original") == ("original", [], 0.5)

    def test_missing_keys_use_defaults(self, corrector):
        """A JSON object without fields keeps the original text and default confidence."""
        assert corrector._parse_llm_response("{}", "original") == ("original", [], 0.8)

    def test_glossary_context_contains_header(self, corrector):
        """The glossary context is labelled so the LLM knows what it is."""
        assert corrector._build_glossary_context().startswith("MEDISCHE WOORDENLIJST:")

    def test_glossary_context_is_empty_without_glossary(self, corrector):
        """No glossary means no glossary context in the prompt."""
        corrector.glossary = None

        assert corrector._build_glossary_context() == ""


class TestCorrectorCorrect:
    @pytest.fixture
    def corrector(self):
        corrector = Corrector(model="test-model")
        corrector._client = MagicMock()
        return corrector

    @pytest.mark.parametrize("text", ["", "   "], ids=["empty", "whitespace"])
    def test_blank_text_is_returned_unchanged(self, corrector, text):
        """Blank input never calls the LLM."""
        result = corrector.correct(text)

        assert result.corrected_text == text
        corrector._client.generate.assert_not_called()

    def test_disabled_config_skips_llm(self, corrector):
        """With correction disabled the text is untouched and the LLM is not called."""
        result = corrector.correct("hartslag", config=CorrectionConfig(enabled=False))

        assert result.corrected_text == "hartslag"
        assert result.correction_confidence == 1.0
        corrector._client.generate.assert_not_called()

    def test_successful_correction_returns_llm_edits(self, corrector):
        """The corrected text, edits and confidence come from the parsed LLM response."""
        corrector._client.generate.return_value = {"response": '{"corrected_text": "hartslag", "edits": [], "confidence": 0.95}'}

        result = corrector.correct(
            "hart slag",
            role=UserRole.PATIENT,
            conversation_context=[{"role": "user", "content": "earlier"}],
        )

        assert result.original_text == "hart slag"
        assert result.corrected_text == "hartslag"
        assert result.correction_confidence == 0.95
        prompt = corrector._client.generate.call_args.kwargs["prompt"]
        assert "hart slag" in prompt
        assert "RECENTE GESPREKSCONTEXT" in prompt

    def test_llm_failure_returns_original_with_zero_confidence(self, corrector):
        """An LLM error must not lose the user's text."""
        corrector._client.generate.side_effect = ConnectionError("ollama down")

        result = corrector.correct("hart slag")

        assert result.corrected_text == "hart slag"
        assert result.correction_confidence == 0.0

    def test_client_is_created_lazily(self, monkeypatch):
        """_ensure_client builds the Ollama client once for the configured host."""
        client_cls = MagicMock()
        monkeypatch.setitem(sys.modules, "ollama", SimpleNamespace(Client=client_cls))
        corrector = Corrector(model="m", ollama_host="http://host:1")

        corrector._ensure_client()
        corrector._ensure_client()

        client_cls.assert_called_once_with(host="http://host:1")

    def test_client_creation_failure_is_wrapped(self, monkeypatch):
        """If the Ollama client cannot be created a RuntimeError explains why."""
        monkeypatch.setitem(sys.modules, "ollama", SimpleNamespace(Client=MagicMock(side_effect=OSError("nope"))))

        with pytest.raises(RuntimeError, match="Could not initialize correction LLM"):
            Corrector(model="m")._ensure_client()
