"""Unified datetime handling system for project time-based analysis.

This module provides consistent datetime operations with standardized format
and smart parsing capabilities for multiple data sources.

See project/team/tasks/TASK-029.md for detailed requirements and implementation decisions.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Amsterdam timezone (handles DST automatically)
AMSTERDAM_TZ = ZoneInfo("Europe/Amsterdam")

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
    "%Y-%m-%d %H:%M:%S%z",  # 2025-06-24 07:30:54+02:00
    "%Y/%m/%d %H:%M:%S%z",  # 2025/06/24 07:30:54+02:00
]


class UnifiedDateTime:
    """Unified datetime handling for project time-based analysis.

    Provides consistent datetime operations with standardized format
    and smart parsing capabilities for multiple data sources.

    The class ensures all datetime operations use the standard format:
    YYYY-MM-DD HH:mm:ss (24-hour clock, seconds accuracy, no timezones)
    """

    # Source-specific format patterns for better detection
    SOURCE_FORMATS = {
        "system_events": [
            "%m/%d/%Y %I:%M:%S %p",  # 5/9/2025 8:08:14 PM
            "%Y/%m/%d %H:%M:%S",  # 2025/06/24 07:30:54
        ],
        "git_commits": [
            "%Y-%m-%dT%H:%M:%S%z",  # 2025-06-24T07:30:54+02:00
            "%Y-%m-%dT%H:%M:%S",  # 2025-06-24T07:30:54
        ],
        "standard": [
            "%Y-%m-%d %H:%M:%S",  # 2025-06-24 07:30:54
            "%Y-%m-%dT%H:%M:%S",  # 2025-06-24T07:30:54
        ],
    }

    def __init__(self, datetime_input: Union[str, datetime, None] = None, source_type: str = None):
        """Initialize with flexible input types.

        Args:
            datetime_input: String, datetime object, or None for current time
            source_type: Optional hint about data source type for better format detection
        """
        self._datetime: Optional[datetime] = None
        self._is_valid: bool = False
        self._detected_format: Optional[str] = None
        self._confidence_score: float = 0.0

        if datetime_input is None:
            # Use current time if no input provided
            self._datetime = datetime.now()
            self._is_valid = True
        elif isinstance(datetime_input, datetime):
            # Handle datetime object input
            self._datetime = datetime_input
            self._is_valid = True
        elif isinstance(datetime_input, str):
            # Parse string input with smart detection
            self._parse_string_with_detection(datetime_input, source_type)
        else:
            logger.warning(f"Unsupported datetime input type: {type(datetime_input)}")
            self._is_valid = False

    def _parse_string_with_detection(self, dt_str: str, source_type: str = None) -> None:
        """Parse datetime string with smart format detection and confidence scoring.

        Args:
            dt_str: DateTime string to parse
            source_type: Optional hint about data source type
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

        # Use smart detection with confidence scoring
        detection_result = self._detect_datetime_format(clean_datetime, source_type)

        if detection_result:
            self._datetime = detection_result["parsed"]
            self._detected_format = detection_result["format"]
            self._confidence_score = detection_result["confidence"]
            self._is_valid = True
            logger.debug(f"Parsed '{dt_str}' using format '{self._detected_format}' with confidence {self._confidence_score:.2f}")
        else:
            logger.warning(f"Could not parse datetime: {dt_str}")
            self._is_valid = False

    def _detect_datetime_format(self, datetime_str: str, source_type: str = None) -> Optional[Dict[str, Any]]:
        """Detect datetime format with confidence scoring.

        Args:
            datetime_str: Input datetime string
            source_type: Optional hint about data source type

        Returns:
            Dictionary with detected format, confidence score, and parsed datetime, or None if no format matches
        """
        candidates = []

        # Get relevant format patterns based on source type
        if source_type and source_type in self.SOURCE_FORMATS:
            patterns = self.SOURCE_FORMATS[source_type] + SUPPORTED_FORMATS
        else:
            patterns = SUPPORTED_FORMATS

        # Remove duplicates while preserving order
        patterns = list(dict.fromkeys(patterns))

        for pattern in patterns:
            try:
                parsed = datetime.strptime(datetime_str, pattern)
                confidence = self._calculate_confidence(datetime_str, pattern, parsed)
                candidates.append({"format": pattern, "confidence": confidence, "parsed": parsed, "source_type": source_type})
            except ValueError:
                continue

        # Try parsing with +0100/+0200 format (without colon)
        # Pattern: YYYY-MM-DD HH:MM:SS+0100 or YYYY-MM-DD HH:MM:SS+0200
        tz_offset_pattern = re.match(r"^(.+?)([+-])(\d{4})$", datetime_str)
        if tz_offset_pattern:
            base_str, sign, offset_str = tz_offset_pattern.groups()
            # Try parsing base datetime
            for base_pattern in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    base_dt = datetime.strptime(base_str, base_pattern)
                    # Parse offset (e.g., +0100 -> +01:00)
                    hours = int(offset_str[:2])
                    minutes = int(offset_str[2:])
                    offset = timedelta(hours=hours, minutes=minutes) if sign == "+" else timedelta(hours=-hours, minutes=-minutes)
                    tz = timezone(offset)
                    parsed = base_dt.replace(tzinfo=tz)
                    confidence = self._calculate_confidence(datetime_str, f"{base_pattern}+offset", parsed)
                    candidates.append(
                        {"format": f"{base_pattern}+offset", "confidence": confidence, "parsed": parsed, "source_type": source_type}
                    )
                    break
                except ValueError:
                    continue

        # Try ISO format parsing as fallback
        try:
            parsed = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            confidence = self._calculate_confidence(datetime_str, "ISO", parsed)
            candidates.append({"format": "ISO", "confidence": confidence, "parsed": parsed, "source_type": source_type})
        except ValueError:
            pass

        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x["confidence"])
            return best

        return None

    def _calculate_confidence(self, datetime_str: str, format_str: str, parsed: datetime) -> float:
        """Calculate confidence score for format detection.

        Args:
            datetime_str: Original datetime string
            format_str: Format string used for parsing
            parsed: Parsed datetime object

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 1.0

        # Penalize formats that don't use all characters
        if format_str != "ISO" and len(datetime_str) != len(parsed.strftime(format_str)):
            score *= 0.8

        # Bonus for formats that match expected patterns
        if re.match(r"^\d{4}-\d{2}-\d{2}", datetime_str):
            score *= 1.1  # ISO-like format bonus

        # Penalize very old or future dates
        current_year = datetime.now().year
        if parsed.year < 2020 or parsed.year > current_year + 1:
            score *= 0.7

        # Bonus for source-specific formats
        if format_str in [fmt for formats in self.SOURCE_FORMATS.values() for fmt in formats]:
            score *= 1.05

        return min(score, 1.0)  # Cap at 1.0

    def _parse_string(self, dt_str: str) -> None:
        """Parse datetime string with multiple format support (legacy method).

        Args:
            dt_str: DateTime string to parse
        """
        self._parse_string_with_detection(dt_str)

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

        # Convert to timezone-naive datetime (local time)
        if self._datetime.tzinfo is not None:
            return self._datetime.replace(tzinfo=None)
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

    def get_detected_format(self) -> Optional[str]:
        """Get the detected format used for parsing.

        Returns:
            Format string used for parsing, or None if not parsed or invalid
        """
        return self._detected_format

    def get_confidence_score(self) -> float:
        """Get the confidence score for format detection.

        Returns:
            Confidence score between 0.0 and 1.0
        """
        return self._confidence_score

    @classmethod
    def detect_format(cls, datetime_str: str, source_type: str = None) -> Optional[str]:
        """Detect the most likely datetime format for the input string.

        Args:
            datetime_str: Input datetime string
            source_type: Optional hint about data source type

        Returns:
            Detected format string or None if no format matches
        """
        instance = cls(datetime_str, source_type)
        return instance.get_detected_format()

    @classmethod
    def parse_with_detection(cls, datetime_str: str, source_type: str = None) -> Optional[datetime]:
        """Parse datetime string with automatic format detection.

        Args:
            datetime_str: Input datetime string
            source_type: Optional hint about data source type

        Returns:
            Parsed datetime object or None if parsing fails
        """
        instance = cls(datetime_str, source_type)
        if instance.is_valid():
            return instance.to_datetime()
        return None

    @classmethod
    def validate_format(cls, datetime_str: str, format_str: str) -> bool:
        """Validate if datetime string matches the specified format.

        Args:
            datetime_str: Input datetime string
            format_str: Format string to validate against

        Returns:
            True if string matches format, False otherwise
        """
        try:
            datetime.strptime(datetime_str, format_str)
            return True
        except ValueError:
            return False

    @classmethod
    def get_detection_confidence(cls, datetime_str: str, format_str: str) -> float:
        """Get confidence score for format detection.

        Args:
            datetime_str: Input datetime string
            format_str: Format string to test

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            parsed = datetime.strptime(datetime_str, format_str)
            instance = cls()
            return instance._calculate_confidence(datetime_str, format_str, parsed)
        except ValueError:
            return 0.0

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


def parse_datetime_with_timezone(dt_str: str, default_tz: ZoneInfo = AMSTERDAM_TZ) -> Optional[datetime]:
    """Parse datetime string with timezone support, returning timezone-aware datetime.

    Supports formats including:
    - Standard formats: YYYY-MM-DD HH:MM:SS, YYYY/MM/DD HH:MM:SS
    - ISO formats: YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SS+02:00
    - Timezone offsets: +0100, +0200 (without colon)
    - AM/PM formats: M/D/YYYY H:MM:SS AM/PM

    If timezone information is missing, assumes default_tz (default: Amsterdam).

    Args:
        dt_str: DateTime string in various formats
        default_tz: Default timezone to use if timezone info is missing (default: Europe/Amsterdam)

    Returns:
        Timezone-aware datetime object or None if parsing fails
    """
    if not dt_str or dt_str.strip() == "":
        return None

    # Clean the datetime string
    clean_datetime = dt_str.strip()
    if clean_datetime.startswith('"'):
        clean_datetime = clean_datetime[1:]
    if clean_datetime.endswith('"'):
        clean_datetime = clean_datetime[:-1]
    if clean_datetime.startswith("\ufeff"):
        clean_datetime = clean_datetime[1:]

    if not clean_datetime:
        return None

    unified_dt = UnifiedDateTime(clean_datetime)
    if not unified_dt.is_valid():
        return None

    # Get the parsed datetime (may be timezone-aware or naive)
    dt = unified_dt._datetime
    if dt is None:
        return None

    # If timezone-naive, assume default timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)
    else:
        # If timezone-aware, convert to default timezone
        dt = dt.astimezone(default_tz)

    return dt


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


class DataSourceParser:
    """Parser for specific data sources with format hints.

    This class provides source-specific datetime parsing with optimized
    format detection for different data sources.
    """

    def __init__(self, source_type: str):
        """Initialize with data source type.

        Args:
            source_type: Type of data source ('system_events', 'git_commits', 'standard')
        """
        self.source_type = source_type
        self.parser = UnifiedDateTime

    def parse_system_event_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse system event timestamp with source-specific logic.

        Args:
            timestamp_str: System event timestamp string

        Returns:
            Parsed datetime object or None if parsing fails
        """
        return self.parser.parse_with_detection(timestamp_str, "system_events")

    def parse_git_commit_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse git commit timestamp with timezone handling.

        Args:
            timestamp_str: Git commit timestamp string

        Returns:
            Parsed datetime object or None if parsing fails
        """
        return self.parser.parse_with_detection(timestamp_str, "git_commits")

    def parse_csv_timestamp(self, timestamp_str: str, column_name: str = None) -> Optional[datetime]:
        """Parse CSV timestamp with column name hints.

        Args:
            timestamp_str: CSV timestamp string
            column_name: Optional column name for additional context

        Returns:
            Parsed datetime object or None if parsing fails
        """
        # Use source type hint if available, otherwise use standard parsing
        source_hint = self.source_type if self.source_type in UnifiedDateTime.SOURCE_FORMATS else None
        return self.parser.parse_with_detection(timestamp_str, source_hint)

    def parse_json_timestamp(self, timestamp_str: str, field_name: str = None) -> Optional[datetime]:
        """Parse JSON timestamp with field name hints.

        Args:
            timestamp_str: JSON timestamp string
            field_name: Optional field name for additional context

        Returns:
            Parsed datetime object or None if parsing fails
        """
        # Use source type hint if available, otherwise use standard parsing
        source_hint = self.source_type if self.source_type in UnifiedDateTime.SOURCE_FORMATS else None
        return self.parser.parse_with_detection(timestamp_str, source_hint)
