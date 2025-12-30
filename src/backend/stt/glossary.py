"""Medical terminology glossary for STT correction.

This module provides a glossary of common medical terms, abbreviations,
and their correct spellings to assist with STT correction.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Default glossary path
GLOSSARY_PATH = os.getenv("STT_GLOSSARY_PATH", None)


class MedicalGlossary:
    """Medical terminology glossary for STT correction assistance."""

    def __init__(self, glossary_path: str | Path | None = None):
        """Initialize the glossary.

        Args:
            glossary_path: Path to custom glossary JSON file.
                          If None, uses built-in glossary.
        """
        self.terms: dict[str, str] = {}
        self.abbreviations: dict[str, str] = {}
        self.common_corrections: dict[str, str] = {}

        # Load built-in glossary
        self._load_builtin_glossary()

        # Load custom glossary if provided
        if glossary_path:
            self._load_custom_glossary(Path(glossary_path))

    def _load_builtin_glossary(self) -> None:
        """Load the built-in medical glossary."""
        # Common medical terms (Dutch + English)
        # Format: phonetic/common misspelling -> correct spelling
        self.terms = {
            # Dutch medical terms
            "bloeddruk": "bloeddruk",
            "hartslag": "hartslag",
            "temperatuur": "temperatuur",
            "medicatie": "medicatie",
            "diagnose": "diagnose",
            "symptomen": "symptomen",
            "behandeling": "behandeling",
            "pijnstiller": "pijnstiller",
            "antibiotica": "antibiotica",
            "recept": "recept",
            "huisarts": "huisarts",
            "specialist": "specialist",
            "ziekenhuis": "ziekenhuis",
            "operatie": "operatie",
            "onderzoek": "onderzoek",
            # Common English medical terms
            "blood pressure": "blood pressure",
            "heart rate": "heart rate",
            "temperature": "temperature",
            "medication": "medication",
            "diagnosis": "diagnosis",
            "symptoms": "symptoms",
            "treatment": "treatment",
            "prescription": "prescription",
            "antibiotic": "antibiotic",
            # Body parts (Dutch)
            "hoofd": "hoofd",
            "borst": "borst",
            "buik": "buik",
            "rug": "rug",
            "arm": "arm",
            "been": "been",
            "knie": "knie",
            "enkel": "enkel",
            # Common conditions (Dutch)
            "diabetes": "diabetes",
            "hypertensie": "hypertensie",
            "astma": "astma",
            "allergie": "allergie",
            "infectie": "infectie",
            "ontsteking": "ontsteking",
            "griep": "griep",
            "verkoudheid": "verkoudheid",
        }

        # Medical abbreviations
        self.abbreviations = {
            # Dutch
            "mg": "mg",
            "ml": "ml",
            "mmol": "mmol",
            "mmhg": "mmHg",
            "bpm": "bpm",
            "x": "x",  # times (e.g., 2x per dag)
            "dd": "dd",  # per dag
            "po": "p.o.",  # per os
            "iv": "i.v.",  # intraveneus
            "im": "i.m.",  # intramusculair
            "sc": "s.c.",  # subcutaan
            # English
            "bp": "BP",  # blood pressure
            "hr": "HR",  # heart rate
            "rr": "RR",  # respiratory rate
            "spo2": "SpO2",  # oxygen saturation
            "ecg": "ECG",
            "ekg": "EKG",
            "mri": "MRI",
            "ct": "CT",
        }

        # Common STT corrections (what Whisper often mishears -> correct)
        self.common_corrections = {
            # Dutch
            "patiënte": "patiënt",
            "patiente": "patiënt",
            "patienten": "patiënten",
            "dokter": "dokter",
            "docter": "dokter",
            "medicijnen": "medicijnen",
            "medicijn": "medicijn",
            # Numbers and dosages often get confused
            "eenmaal": "1x",
            "tweemaal": "2x",
            "driemaal": "3x",
            "viermaal": "4x",
            "per dag": "per dag",
            "per week": "per week",
            # English common mishearings
            "patients": "patient's",
            "patience": "patient",
        }

        logger.info(
            f"Loaded built-in glossary: {len(self.terms)} terms, "
            f"{len(self.abbreviations)} abbreviations, {len(self.common_corrections)} corrections"
        )

    def _load_custom_glossary(self, path: Path) -> None:
        """Load a custom glossary from a JSON file.

        Expected format:
        {
            "terms": {"term": "correct_spelling", ...},
            "abbreviations": {"abbr": "expansion", ...},
            "corrections": {"misspelling": "correct", ...}
        }
        """
        if not path.exists():
            logger.warning(f"Custom glossary not found: {path}")
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            if "terms" in data:
                self.terms.update(data["terms"])
            if "abbreviations" in data:
                self.abbreviations.update(data["abbreviations"])
            if "corrections" in data:
                self.common_corrections.update(data["corrections"])

            logger.info(f"Loaded custom glossary from {path}")
        except Exception as e:
            logger.error(f"Failed to load custom glossary: {e}")

    def get_correction_context(self) -> str:
        """Get a formatted string of glossary terms for LLM context.

        Returns a compact representation suitable for including in an LLM prompt.
        """
        context_parts = []

        # Add key medical terms
        if self.terms:
            terms_sample = list(self.terms.keys())[:30]  # Limit to avoid token overflow
            context_parts.append(f"Medical terms: {', '.join(terms_sample)}")

        # Add abbreviations
        if self.abbreviations:
            abbr_formatted = [f"{k}={v}" for k, v in list(self.abbreviations.items())[:20]]
            context_parts.append(f"Abbreviations: {', '.join(abbr_formatted)}")

        return "\n".join(context_parts)

    def find_term(self, text: str) -> list[str]:
        """Find medical terms in the text.

        Args:
            text: Text to search for medical terms

        Returns:
            List of recognized medical terms found in the text
        """
        text_lower = text.lower()
        found_terms = []

        for term in self.terms:
            if term.lower() in text_lower:
                found_terms.append(term)

        return found_terms

    def suggest_correction(self, word: str) -> str | None:
        """Suggest a correction for a potentially misspelled word.

        Args:
            word: Word to check

        Returns:
            Corrected word if a correction is found, None otherwise
        """
        word_lower = word.lower()

        # Check common corrections
        if word_lower in self.common_corrections:
            return self.common_corrections[word_lower]

        # Check abbreviations
        if word_lower in self.abbreviations:
            return self.abbreviations[word_lower]

        return None


# Global glossary instance
_glossary: MedicalGlossary | None = None


def get_glossary() -> MedicalGlossary:
    """Get the global glossary instance (lazy initialization)."""
    global _glossary
    if _glossary is None:
        _glossary = MedicalGlossary(GLOSSARY_PATH)
    return _glossary
