"""Context-aware LLM correction for STT transcriptions.

This module provides context-aware correction of STT transcriptions using
a local LLM (Ollama), incorporating conversation context, medical glossary,
and role-specific terminology.
"""

import json
import logging
import os
import re
from typing import Any

from backend.stt.glossary import MedicalGlossary, get_glossary
from backend.stt.models import CorrectionConfig, CorrectionResult, UserRole

logger = logging.getLogger(__name__)

# Correction model configuration
CORRECTION_MODEL = os.getenv("STT_CORRECTION_MODEL", "mistral:latest")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


# Correction prompt templates
CONSERVATIVE_PROMPT_TEMPLATE = """Je bent een medische transcriptie-corrector. Corrigeer ALLEEN duidelijke transcriptiefouten in de onderstaande tekst.

REGELS (STRIKT):
1. Behoud de exacte betekenis - voeg GEEN nieuwe informatie toe
2. Corrigeer alleen duidelijke spelfouten en verkeerd verstane woorden
3. Behoud getallen, metingen en doseringen exact
4. Corrigeer medische termen naar de correcte spelling
5. Maak minimale wijzigingen - bij twijfel, laat ongewijzigd
6. PII (patiëntnamen, etc.) is toegestaan en moet behouden blijven

{role_context}

{glossary_context}

{conversation_context}

TRANSCRIPTIE OM TE CORRIGEREN:
"{text}"

Geef de gecorrigeerde tekst terug in het volgende JSON-formaat:
{{
    "corrected_text": "de gecorrigeerde tekst hier",
    "edits": [
        {{"original": "origineel woord", "corrected": "gecorrigeerd woord", "reason": "korte reden"}}
    ],
    "confidence": 0.95
}}

Als er geen correcties nodig zijn, geef dan de originele tekst terug met een lege edits lijst.
Antwoord ALLEEN met de JSON, geen andere tekst."""

AGGRESSIVE_PROMPT_TEMPLATE = """Je bent een medische transcriptie-assistent. Verbeter de onderstaande transcriptie voor leesbaarheid en correctheid.

REGELS:
1. Corrigeer spelfouten en grammatica
2. Verbeter zinsstructuur waar nodig
3. Gebruik correcte medische terminologie
4. Behoud de kern van de boodschap
5. Getallen, metingen en doseringen moeten exact behouden blijven
6. PII (patiëntnamen, etc.) is toegestaan en moet behouden blijven

{role_context}

{glossary_context}

{conversation_context}

TRANSCRIPTIE OM TE VERBETEREN:
"{text}"

Geef de verbeterde tekst terug in het volgende JSON-formaat:
{{
    "corrected_text": "de verbeterde tekst hier",
    "edits": [
        {{"original": "origineel", "corrected": "verbeterd", "reason": "korte reden"}}
    ],
    "confidence": 0.90
}}

Antwoord ALLEEN met de JSON, geen andere tekst."""


class Corrector:
    """Context-aware corrector for STT transcriptions using local LLM."""

    def __init__(
        self,
        model: str = CORRECTION_MODEL,
        ollama_host: str = OLLAMA_HOST,
        glossary: MedicalGlossary | None = None,
    ):
        """Initialize the corrector.

        Args:
            model: Ollama model to use for correction
            ollama_host: Ollama server URL
            glossary: Medical glossary for term recognition
        """
        self.model = model
        self.ollama_host = ollama_host
        self.glossary = glossary or get_glossary()
        self._client = None

    def _ensure_client(self) -> None:
        """Lazy-initialize the Ollama client."""
        if self._client is None:
            try:
                import ollama

                self._client = ollama.Client(host=self.ollama_host)
                logger.info(f"Initialized Ollama client for correction: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama client: {e}")
                raise RuntimeError(f"Could not initialize correction LLM: {e}") from e

    def _build_role_context(self, role: UserRole) -> str:
        """Build role-specific context for the correction prompt."""
        role_contexts = {
            UserRole.GP: (
                "CONTEXT: Dit is een transcriptie van een huisarts (GP). "
                "Verwacht medische terminologie, diagnoses, behandelplannen en patiëntbesprekingen. "
                "De toon is professioneel en klinisch."
            ),
            UserRole.PATIENT: (
                "CONTEXT: Dit is een transcriptie van een patiënt. "
                "Verwacht beschrijvingen van symptomen in lekentaal, vragen over gezondheid, "
                "en mogelijk onnauwkeurige medische termen. De toon is informeel."
            ),
            UserRole.ADMIN: ("CONTEXT: Dit is een transcriptie van een beheerder. De inhoud kan administratief of technisch zijn."),
        }
        return role_contexts.get(role, "")

    def _build_conversation_context(self, messages: list[dict[str, str]], max_messages: int = 5) -> str:
        """Build conversation context from recent messages."""
        if not messages:
            return ""

        # Take the most recent messages
        recent = messages[-max_messages:] if len(messages) > max_messages else messages

        context_lines = ["RECENTE GESPREKSCONTEXT:"]
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Limit content length
            context_lines.append(f"- {role}: {content}")

        return "\n".join(context_lines)

    def _build_glossary_context(self) -> str:
        """Build glossary context for the prompt."""
        if not self.glossary:
            return ""

        return f"MEDISCHE WOORDENLIJST:\n{self.glossary.get_correction_context()}"

    def _parse_llm_response(self, response: str, original_text: str) -> tuple[str, list[dict[str, str]], float]:
        """Parse the LLM response to extract corrected text and edits.

        Returns:
            Tuple of (corrected_text, edits_list, confidence)
        """
        try:
            # Try to extract JSON from the response
            # Handle cases where LLM adds extra text around JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                corrected_text = data.get("corrected_text", original_text)
                edits = data.get("edits", [])
                confidence = float(data.get("confidence", 0.8))

                return corrected_text, edits, confidence
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")

        # Fallback: return original text with no edits
        return original_text, [], 0.5

    def correct(
        self,
        text: str,
        role: UserRole = UserRole.GP,
        conversation_context: list[dict[str, str]] | None = None,
        config: CorrectionConfig | None = None,
        session_metadata: dict[str, Any] | None = None,
    ) -> CorrectionResult:
        """Apply context-aware correction to transcribed text.

        Args:
            text: Transcribed text to correct
            role: User role for context
            conversation_context: Recent conversation messages
            config: Correction configuration
            session_metadata: Additional session metadata

        Returns:
            CorrectionResult with corrected text and edit details
        """
        if not text or not text.strip():
            return CorrectionResult(
                original_text=text,
                corrected_text=text,
                edits_made=[],
                correction_confidence=1.0,
                glossary_matches=[],
            )

        config = config or CorrectionConfig()
        conversation_context = conversation_context or []

        if not config.enabled:
            return CorrectionResult(
                original_text=text,
                corrected_text=text,
                edits_made=[],
                correction_confidence=1.0,
                glossary_matches=self.glossary.find_term(text) if self.glossary else [],
            )

        self._ensure_client()

        # Build prompt
        template = CONSERVATIVE_PROMPT_TEMPLATE if config.conservative_mode else AGGRESSIVE_PROMPT_TEMPLATE

        role_context = self._build_role_context(role)
        glossary_context = self._build_glossary_context() if config.use_glossary else ""
        conv_context = (
            self._build_conversation_context(conversation_context, config.max_context_messages)
            if config.use_conversation_context
            else ""
        )

        prompt = template.format(
            text=text,
            role_context=role_context,
            glossary_context=glossary_context,
            conversation_context=conv_context,
        )

        try:
            logger.debug(f"Sending correction request to Ollama: {len(text)} chars")

            response = self._client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temperature for consistent corrections
                    "top_p": 0.9,
                    "num_predict": 1024,
                },
            )

            response_text = response.get("response", "")
            corrected_text, edits, confidence = self._parse_llm_response(response_text, text)

            # Find glossary matches in the corrected text
            glossary_matches = self.glossary.find_term(corrected_text) if self.glossary else []

            logger.info(f"Correction complete: {len(edits)} edits, confidence: {confidence:.2f}")

            return CorrectionResult(
                original_text=text,
                corrected_text=corrected_text,
                edits_made=edits,
                correction_confidence=confidence,
                glossary_matches=glossary_matches,
            )

        except Exception as e:
            logger.error(f"Correction failed: {e}")
            # Return original text on failure
            return CorrectionResult(
                original_text=text,
                corrected_text=text,
                edits_made=[],
                correction_confidence=0.0,
                glossary_matches=self.glossary.find_term(text) if self.glossary else [],
            )

    def get_model_info(self) -> dict:
        """Get information about the correction model."""
        return {
            "model": self.model,
            "ollama_host": self.ollama_host,
            "is_initialized": self._client is not None,
        }


# Global corrector instance
_corrector: Corrector | None = None


def get_corrector() -> Corrector:
    """Get the global corrector instance (lazy initialization)."""
    global _corrector
    if _corrector is None:
        _corrector = Corrector()
    return _corrector
