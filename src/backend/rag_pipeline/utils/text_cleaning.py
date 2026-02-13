"""Text cleaning utilities for document processing.

This module provides functions to clean and normalize text content
from documents before chunking and embedding.
"""

import re
import unicodedata


def clean_text(text: str, aggressive: bool = False) -> str:
    """Clean and normalize text content.

    Args:
        text: Raw text to clean
        aggressive: Whether to apply aggressive cleaning (removes more content)

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Convert to string if needed
    text = str(text)

    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    if aggressive:
        # Aggressive cleaning - remove more problematic content
        text = clean_text_aggressive(text)
    else:
        # Standard cleaning - preserve most content
        text = clean_text_standard(text)

    return text


def clean_text_standard(text: str) -> str:
    """Apply standard text cleaning while preserving most content.

    Args:
        text: Text to clean

    Returns:
        Standard cleaned text
    """
    # Remove excessive newlines and spaces
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # More than 2 consecutive newlines
    text = re.sub(r" {3,}", " ", text)  # More than 2 consecutive spaces

    # Remove control characters except newlines and tabs
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive punctuation (but keep meaningful ones)
    text = re.sub(r"[.!?]{3,}", "...", text)  # Multiple punctuation to ellipsis

    return text


def clean_text_aggressive(text: str) -> str:
    """Apply aggressive text cleaning for problematic content.

    Args:
        text: Text to clean aggressively

    Returns:
        Aggressively cleaned text
    """
    # Apply standard cleaning first
    text = clean_text_standard(text)

    # Remove mathematical symbols and special characters that might cause issues
    # Keep basic math operators but remove complex symbols
    text = re.sub(r"[𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒭𝒖𝒗𝒘𝒙𝒚𝒛𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁]", "", text)

    # Remove other problematic Unicode characters
    text = re.sub(r"[^\x20-\x7E\n\t]", "", text)  # Keep only printable ASCII + newlines/tabs

    # Remove excessive whitespace again
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_chunk_text(text: str, min_length: int = 10) -> str | None:
    """Clean chunk text and validate quality.

    Args:
        text: Raw chunk text
        min_length: Minimum acceptable text length

    Returns:
        Cleaned text if it meets quality standards, None otherwise
    """
    if not text:
        return None

    # Clean the text
    cleaned = clean_text(text, aggressive=False)

    # Check if cleaned text meets quality standards
    if len(cleaned.strip()) < min_length:
        return None

    # Check if text is mostly whitespace or special characters
    alphanumeric_ratio = len(re.findall(r"[a-zA-Z0-9]", cleaned)) / len(cleaned) if cleaned else 0
    if alphanumeric_ratio < 0.1:  # Less than 10% alphanumeric
        return None

    return cleaned


def validate_chunk_quality(chunk_text: str, min_length: int = 10, min_alphanumeric_ratio: float = 0.1) -> bool:
    """Validate chunk text quality.

    Args:
        chunk_text: Text to validate
        min_length: Minimum acceptable text length
        min_alphanumeric_ratio: Minimum ratio of alphanumeric characters

    Returns:
        True if chunk meets quality standards
    """
    if not chunk_text or len(chunk_text.strip()) < min_length:
        return False

    # Calculate alphanumeric ratio
    alphanumeric_count = len(re.findall(r"[a-zA-Z0-9]", chunk_text))
    total_length = len(chunk_text)
    alphanumeric_ratio = alphanumeric_count / total_length if total_length > 0 else 0

    return alphanumeric_ratio >= min_alphanumeric_ratio


def get_text_statistics(text: str) -> dict:
    """Get statistics about text content.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with text statistics
    """
    if not text:
        return {"length": 0, "word_count": 0, "alphanumeric_ratio": 0.0, "whitespace_ratio": 0.0, "special_char_ratio": 0.0}

    total_length = len(text)
    word_count = len(text.split())
    alphanumeric_count = len(re.findall(r"[a-zA-Z0-9]", text))
    whitespace_count = len(re.findall(r"\s", text))
    special_char_count = total_length - alphanumeric_count - whitespace_count

    return {
        "length": total_length,
        "word_count": word_count,
        "alphanumeric_ratio": alphanumeric_count / total_length if total_length > 0 else 0.0,
        "whitespace_ratio": whitespace_count / total_length if total_length > 0 else 0.0,
        "special_char_ratio": special_char_count / total_length if total_length > 0 else 0.0,
    }
