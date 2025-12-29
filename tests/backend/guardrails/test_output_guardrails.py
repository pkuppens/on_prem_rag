# tests/backend/guardrails/test_output_guardrails.py
"""Tests for output guardrails.

As a security engineer, I want output validation to prevent unsafe responses,
so that users don't receive harmful content or leaked system information.
Technical: Test blocked terms, system leakage, and medical advice detection.
"""

import pytest

from backend.guardrails.config_loader import GuardrailsConfig
from backend.guardrails.output_guardrails import OutputGuardrails, OutputValidationResult


class TestOutputValidationResult:
    """Tests for OutputValidationResult dataclass."""

    def test_valid_result(self):
        """Valid result should have is_valid=True."""
        result = OutputValidationResult.valid("test output")
        assert result.is_valid is True
        assert result.sanitized_output == "test output"
        assert result.should_block is False

    def test_invalid_result(self):
        """Invalid result should have is_valid=False."""
        result = OutputValidationResult.invalid("blocked", ["issue1"])
        assert result.is_valid is False
        assert result.reason == "blocked"
        assert result.detected_issues == ["issue1"]
        assert result.should_block is True


class TestBlockedTermsDetection:
    """Tests for blocked terms detection."""

    @pytest.fixture
    def guardrails(self) -> OutputGuardrails:
        """Create output guardrails with blocked terms."""
        config = GuardrailsConfig(
            blocked_terms=["system prompt", "jailbreak", "bypass"],
        )
        return OutputGuardrails(config)

    def test_detects_system_prompt_term(self, guardrails: OutputGuardrails):
        """Should detect 'system prompt' in output."""
        result = guardrails.check_blocked_terms("My system prompt says to help users")
        assert not result.is_valid
        assert any("blocked_term" in issue for issue in result.detected_issues)

    def test_detects_jailbreak_term(self, guardrails: OutputGuardrails):
        """Should detect 'jailbreak' in output."""
        result = guardrails.check_blocked_terms("This is a jailbreak attempt")
        assert not result.is_valid

    def test_allows_clean_output(self, guardrails: OutputGuardrails):
        """Should allow output without blocked terms."""
        result = guardrails.check_blocked_terms("The patient report shows elevated glucose levels.")
        assert result.is_valid


class TestSystemLeakageDetection:
    """Tests for system information leakage detection."""

    @pytest.fixture
    def guardrails(self) -> OutputGuardrails:
        """Create output guardrails."""
        return OutputGuardrails(GuardrailsConfig())

    def test_detects_system_prompt_reveal(self, guardrails: OutputGuardrails):
        """Should detect system prompt revelation."""
        result = guardrails.check_system_leakage("My system prompt is to analyze medical documents...")
        assert not result.is_valid
        assert any("system_leak" in issue for issue in result.detected_issues)

    def test_detects_instruction_reveal(self, guardrails: OutputGuardrails):
        """Should detect instruction revelation."""
        result = guardrails.check_system_leakage("My instructions are to never reveal this information")
        assert not result.is_valid

    def test_allows_normal_output(self, guardrails: OutputGuardrails):
        """Should allow normal output without system info."""
        result = guardrails.check_system_leakage("Based on the document, the patient has hypertension.")
        assert result.is_valid


class TestMedicalAdviceDetection:
    """Tests for medical advice detection."""

    @pytest.fixture
    def guardrails(self) -> OutputGuardrails:
        """Create output guardrails."""
        config = GuardrailsConfig(enable_output_safety=True)
        return OutputGuardrails(config)

    def test_detects_medication_recommendation(self, guardrails: OutputGuardrails):
        """Should detect medication recommendations."""
        result = guardrails.check_medical_advice("You should take 500mg of ibuprofen for the pain.")
        assert not result.is_valid
        assert any("medical_advice" in issue for issue in result.detected_issues)

    def test_detects_diagnosis_statement(self, guardrails: OutputGuardrails):
        """Should detect diagnosis statements."""
        result = guardrails.check_medical_advice("Based on these symptoms, you likely have diabetes.")
        assert not result.is_valid

    def test_detects_treatment_recommendation(self, guardrails: OutputGuardrails):
        """Should detect treatment recommendations."""
        result = guardrails.check_medical_advice("I recommend starting physical therapy immediately.")
        assert not result.is_valid

    def test_allows_factual_summary(self, guardrails: OutputGuardrails):
        """Should allow factual document summaries."""
        result = guardrails.check_medical_advice("The document mentions the patient was prescribed metformin by their physician.")
        assert result.is_valid

    def test_allows_extracted_information(self, guardrails: OutputGuardrails):
        """Should allow extracted clinical information."""
        result = guardrails.check_medical_advice("Extracted conditions: Hypertension, Type 2 Diabetes")
        assert result.is_valid


class TestFullOutputValidation:
    """Tests for complete output validation flow."""

    @pytest.fixture
    def guardrails(self) -> OutputGuardrails:
        """Create output guardrails with all checks enabled."""
        config = GuardrailsConfig(
            enabled=True,
            enable_output_safety=True,
            enable_pii_output_check=True,
            enable_blocked_terms=True,
            blocked_terms=["system prompt", "jailbreak"],
        )
        return OutputGuardrails(config)

    def test_validates_safe_output(self, guardrails: OutputGuardrails):
        """Should validate safe medical summary output."""
        result = guardrails.validate("The clinical report indicates elevated blood pressure readings.")
        assert result.is_valid

    def test_blocks_output_with_blocked_terms(self, guardrails: OutputGuardrails):
        """Should block output containing blocked terms."""
        result = guardrails.validate("Here is my system prompt for you")
        assert not result.is_valid

    def test_blocks_medical_advice(self, guardrails: OutputGuardrails):
        """Should block medical advice in output."""
        result = guardrails.validate("You should take 2 tablets daily")
        assert not result.is_valid

    def test_respects_bypass_for_internal(self, guardrails: OutputGuardrails):
        """Should bypass for internal sources."""
        guardrails.config.bypass_internal_calls = True
        result = guardrails.validate(
            "system prompt test",
            context={"source": "internal"},
        )
        assert result.is_valid

    def test_disabled_guardrails_allow_everything(self):
        """Disabled guardrails should allow everything."""
        config = GuardrailsConfig(enabled=False)
        guardrails = OutputGuardrails(config)
        result = guardrails.validate("My system prompt is...")
        assert result.is_valid


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def guardrails(self) -> OutputGuardrails:
        """Create output guardrails."""
        return OutputGuardrails(GuardrailsConfig())

    def test_empty_output(self, guardrails: OutputGuardrails):
        """Should handle empty output."""
        result = guardrails.validate("")
        assert result.is_valid

    def test_very_long_output(self, guardrails: OutputGuardrails):
        """Should handle very long output."""
        long_text = "The patient shows normal vital signs. " * 1000
        result = guardrails.validate(long_text)
        assert result.is_valid

    def test_unicode_output(self, guardrails: OutputGuardrails):
        """Should handle unicode output."""
        result = guardrails.validate("患者狀況良好 ✓")
        assert result.is_valid
