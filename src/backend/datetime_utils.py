"""Unified datetime handling system for project time-based analysis.

This module provides consistent datetime operations with standardized format
and smart parsing capabilities for multiple data sources.

See project/team/tasks/TASK-029.md for detailed requirements and implementation decisions.
"""

import logging
from datetime import datetime, timezone
from typing import Union, Optional, List

logger = logging.getLogger(__name__)

# Standard format used across the project
STANDARD_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ISO format without timezone for string representation
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Supported input formats found in the codebase
SUPPORTED_FORMATS = [
    "%m/%d/%Y %I:%M:%S %p",  # 5/9/2025 8:08:14 PM
    "%Y/%m/%d %H:%M:%S",  # 2025/06/24 07:30:54
    "%Y-%m-%d %H:%M:%S",  # 2025-06-24 07:30:54
    "%Y-%m-%dT%H:%M:%S",  # 2025-06-24T07:30:54
    "%Y-%m-%dT%H:%M:%S%z",  # 2025-06-24T07:30:54+02:00
    "%Y-%m-%dT%H:%M:%S.%f",  # 2025-06-24T07:30:54.123456
    "%Y-%m-%dT%H:%M:%S.%f%z",  # 2025-06-24T07:30:54.123456+02:00
]


class UnifiedDateTime:
    """Unified datetime handling for project time-based analysis.

    Provides consistent datetime operations with standardized format
    and smart parsing capabilities for multiple data sources.

    The class ensures all datetime operations use the standard format:
    YYYY-MM-DD HH:mm:ss (24-hour clock, seconds accuracy, no timezones)
    """

    def __init__(self, datetime_input: Union[str, datetime, None] = None):
        """Initialize with flexible input types.

        Args:
            datetime_input: String, datetime object, or None for current time
        """
        self._datetime: Optional[datetime] = None
        self._is_valid: bool = False

        if datetime_input is None:
            # Use current time if no input provided
            self._datetime = datetime.now()
            self._is_valid = True
        elif isinstance(datetime_input, datetime):
            # Handle datetime object input
            self._datetime = datetime_input
            self._is_valid = True
        elif isinstance(datetime_input, str):
            # Parse string input
            self._parse_string(datetime_input)
        else:
            logger.warning(f"Unsupported datetime input type: {type(datetime_input)}")
            self._is_valid = False

    def _parse_string(self, dt_str: str) -> None:
        """Parse datetime string with multiple format support.

        Args:
            dt_str: DateTime string to parse
        """
        if not dt_str or dt_str.strip() == "":
            logger.warning("Empty datetime string provided")
            self._is_valid = False
            return

        # Clean the datetime string
        clean_datetime = dt_str.strip()
        if clean_datetime.startswith('"'):
            clean_datetime = clean_datetime[1:]
        if clean_datetime.endswith('"'):
            clean_datetime = clean_datetime[:-1]
        # Remove BOM if present
        if clean_datetime.startswith("\ufeff"):
            clean_datetime = clean_datetime[1:]

        if not clean_datetime:
            logger.warning("Empty datetime string after cleaning")
            self._is_valid = False
            return

        # Try each supported format
        for fmt in SUPPORTED_FORMATS:
            try:
                parsed_dt = datetime.strptime(clean_datetime, fmt)
                # Convert to timezone-naive (local) datetime
                if parsed_dt.tzinfo is not None:
                    parsed_dt = parsed_dt.replace(tzinfo=None)
                self._datetime = parsed_dt
                self._is_valid = True
                return
            except ValueError:
                continue

        # Try ISO format parsing as fallback
        try:
            parsed_dt = datetime.fromisoformat(clean_datetime.replace("Z", "+00:00"))
            if parsed_dt.tzinfo is not None:
                parsed_dt = parsed_dt.replace(tzinfo=None)
            self._datetime = parsed_dt
            self._is_valid = True
            return
        except ValueError:
            pass

        logger.warning(f"Could not parse datetime: {dt_str}")
        self._is_valid = False

    def to_standard_format(self) -> str:
        """Return datetime in standard YYYY-MM-DD HH:mm:ss format.

        Returns:
            Standardized datetime string or empty string if invalid
        """
        if not self.is_valid():
            return ""
        return self._datetime.strftime(STANDARD_DATETIME_FORMAT)

    def to_iso_format(self) -> str:
        """Return datetime in ISO format without timezone (YYYY-MM-DDTHH:mm:ss).

        Returns:
            ISO datetime string or empty string if invalid
        """
        if not self.is_valid():
            return ""
        return self._datetime.strftime(ISO_DATETIME_FORMAT)

    def to_datetime(self) -> Optional[datetime]:
        """Return Python datetime object.

        Returns:
            Datetime object or None if invalid
        """
        if not self.is_valid():
            return None
        return self._datetime

    @classmethod
    def parse_flexible(cls, dt_str: str) -> "UnifiedDateTime":
        """Parse datetime string with multiple format support.

        Args:
            dt_str: DateTime string to parse

        Returns:
            UnifiedDateTime instance
        """
        return cls(dt_str)

    def is_valid(self) -> bool:
        """Check if datetime is valid and parseable.

        Returns:
            True if datetime is valid, False otherwise
        """
        return self._is_valid and self._datetime is not None

    def __str__(self) -> str:
        """String representation in ISO format without timezone."""
        return self.to_iso_format()

    def __repr__(self) -> str:
        """Detailed string representation."""
        if self.is_valid():
            return f"UnifiedDateTime('{self.to_iso_format()}')"
        else:
            return "UnifiedDateTime(invalid)"

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, UnifiedDateTime):
            return False
        if not self.is_valid() or not other.is_valid():
            return False
        return self._datetime == other._datetime

    def __lt__(self, other) -> bool:
        """Less than comparison for sorting."""
        if not isinstance(other, UnifiedDateTime):
            return NotImplemented
        if not self.is_valid() or not other.is_valid():
            return False
        return self._datetime < other._datetime

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if not isinstance(other, UnifiedDateTime):
            return NotImplemented
        if not self.is_valid() or not other.is_valid():
            return False
        return self._datetime > other._datetime

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self.__gt__(other) or self.__eq__(other)


def parse_datetime_flexible(dt_str: str) -> Optional[datetime]:
    """Parse datetime string with multiple format support.

    This function provides backward compatibility with existing code
    while using the new UnifiedDateTime system internally.

    Args:
        dt_str: DateTime string in various formats

    Returns:
        datetime object or None if parsing fails
    """
    unified_dt = UnifiedDateTime(dt_str)
    if unified_dt.is_valid():
        return unified_dt.to_datetime()
    return None


def convert_to_standard_format(dt_input: Union[str, datetime]) -> str:
    """Convert datetime input to standard format.

    Args:
        dt_input: String or datetime object to convert

    Returns:
        Standardized datetime string
    """
    unified_dt = UnifiedDateTime(dt_input)
    return unified_dt.to_standard_format()


def validate_datetime_format(dt_str: str) -> bool:
    """Validate if datetime string can be parsed.

    Args:
        dt_str: DateTime string to validate

    Returns:
        True if string can be parsed, False otherwise
    """
    unified_dt = UnifiedDateTime(dt_str)
    return unified_dt.is_valid()
