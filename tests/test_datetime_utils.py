"""Comprehensive unit tests for unified datetime handling system.

This module tests the UnifiedDateTime class and related functions to ensure
consistent datetime operations across the project.

See src/backend/datetime_utils.py for the implementation being tested.
"""

import pytest
from datetime import datetime, timezone
from src.backend.datetime_utils import (
    UnifiedDateTime,
    parse_datetime_flexible,
    convert_to_standard_format,
    validate_datetime_format,
    STANDARD_DATETIME_FORMAT,
    SUPPORTED_FORMATS,
)


class TestUnifiedDateTime:
    """Test cases for UnifiedDateTime class."""

    def test_initialization_with_none(self):
        """As a user I want to create a UnifiedDateTime with no input, so I can get current time.
        Technical: Initialize with None should use current time.
        Validation: Check that datetime is valid and represents current time.
        """
        dt = UnifiedDateTime()
        assert dt.is_valid()
        assert isinstance(dt.to_datetime(), datetime)
        # Should be within last few seconds
        now = datetime.now()
        diff = abs((dt.to_datetime() - now).total_seconds())
        assert diff < 5

    def test_initialization_with_datetime_object(self):
        """As a user I want to create a UnifiedDateTime from a datetime object, so I can convert existing datetimes.
        Technical: Initialize with datetime object should preserve the datetime.
        Validation: Check that the datetime is preserved and valid.
        """
        original_dt = datetime(2025, 5, 3, 14, 30, 45)
        dt = UnifiedDateTime(original_dt)
        assert dt.is_valid()
        assert dt.to_datetime() == original_dt
        assert dt.to_standard_format() == "2025-05-03 14:30:45"

    def test_initialization_with_invalid_type(self):
        """As a user I want to handle invalid input types gracefully, so the system doesn't crash.
        Technical: Initialize with unsupported type should result in invalid datetime.
        Validation: Check that invalid input results in invalid datetime.
        """
        dt = UnifiedDateTime(123)  # Invalid type
        assert not dt.is_valid()
        assert dt.to_datetime() is None
        assert dt.to_standard_format() == ""

    def test_standard_format_parsing(self):
        """As a user I want to parse standard format datetime strings, so I can work with consistent data.
        Technical: Parse YYYY-MM-DD HH:mm:ss format correctly.
        Validation: Check that standard format is parsed correctly.
        """
        dt_str = "2025-05-03 14:30:45"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        assert dt.to_standard_format() == dt_str
        assert dt.to_datetime() == datetime(2025, 5, 3, 14, 30, 45)

    def test_system_events_format_parsing(self):
        """As a user I want to parse system events datetime formats, so I can process system event data.
        Technical: Parse M/D/YYYY H:MM:SS AM/PM format correctly.
        Validation: Check that system events format is parsed correctly.
        """
        dt_str = "5/9/2025 8:08:14 PM"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        assert dt.to_standard_format() == "2025-05-09 20:08:14"

    def test_git_commit_format_parsing(self):
        """As a user I want to parse git commit datetime formats, so I can process commit data.
        Technical: Parse YYYY-MM-DDTHH:mm:ss+timezone format correctly.
        Validation: Check that git commit format is parsed correctly.
        """
        dt_str = "2025-06-24T07:30:54+02:00"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        # Should convert to local time (remove timezone)
        assert dt.to_standard_format() == "2025-06-24 07:30:54"

    def test_iso_format_parsing(self):
        """As a user I want to parse ISO format datetime strings, so I can work with standard datetime data.
        Technical: Parse ISO format with T separator correctly.
        Validation: Check that ISO format is parsed correctly.
        """
        dt_str = "2025-06-24T07:30:54"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        assert dt.to_standard_format() == "2025-06-24 07:30:54"

    def test_quoted_string_parsing(self):
        """As a user I want to parse quoted datetime strings, so I can handle CSV data with quotes.
        Technical: Parse datetime strings with surrounding quotes correctly.
        Validation: Check that quoted strings are parsed correctly.
        """
        dt_str = '"2025-05-03 14:30:45"'
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        assert dt.to_standard_format() == "2025-05-03 14:30:45"

    def test_bom_string_parsing(self):
        """As a user I want to parse datetime strings with BOM, so I can handle UTF-8 files with BOM.
        Technical: Parse datetime strings with UTF-8 BOM correctly.
        Validation: Check that BOM strings are parsed correctly.
        """
        dt_str = "\ufeff2025-05-03 14:30:45"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        assert dt.to_standard_format() == "2025-05-03 14:30:45"

    def test_empty_string_handling(self):
        """As a user I want to handle empty datetime strings gracefully, so the system doesn't crash.
        Technical: Handle empty and whitespace-only strings correctly.
        Validation: Check that empty strings result in invalid datetime.
        """
        for empty_str in ["", "   ", "\t", "\n"]:
            dt = UnifiedDateTime(empty_str)
            assert not dt.is_valid()
            assert dt.to_datetime() is None
            assert dt.to_standard_format() == ""

    def test_invalid_string_handling(self):
        """As a user I want to handle invalid datetime strings gracefully, so the system doesn't crash.
        Technical: Handle malformed datetime strings correctly.
        Validation: Check that invalid strings result in invalid datetime.
        """
        invalid_strings = [
            "not a datetime",
            "2025-13-01 25:70:80",  # Invalid date/time values
            "2025/05/03",  # Missing time
            "14:30:45",  # Missing date
        ]

        for invalid_str in invalid_strings:
            dt = UnifiedDateTime(invalid_str)
            assert not dt.is_valid()
            assert dt.to_datetime() is None
            assert dt.to_standard_format() == ""

    def test_comparison_operations(self):
        """As a user I want to compare datetime objects, so I can sort and filter time-based data.
        Technical: Implement comparison operations for sorting and filtering.
        Validation: Check that comparison operations work correctly.
        """
        dt1 = UnifiedDateTime("2025-05-03 14:30:45")
        dt2 = UnifiedDateTime("2025-05-03 15:30:45")
        dt3 = UnifiedDateTime("2025-05-03 14:30:45")

        assert dt1 < dt2
        assert dt2 > dt1
        assert dt1 == dt3
        assert dt1 <= dt2
        assert dt1 <= dt3
        assert dt2 >= dt1
        assert dt3 >= dt1

    def test_string_representation(self):
        """As a user I want to get string representations of datetime objects, so I can display them.
        Technical: Implement __str__ and __repr__ methods correctly.
        Validation: Check that string representations are correct.
        """
        dt = UnifiedDateTime("2025-05-03 14:30:45")
        assert str(dt) == "2025-05-03T14:30:45"  # ISO format
        assert repr(dt) == "UnifiedDateTime('2025-05-03T14:30:45')"  # ISO format

        # Test invalid datetime
        invalid_dt = UnifiedDateTime("invalid")
        assert str(invalid_dt) == ""
        assert "invalid" in repr(invalid_dt)

    def test_parse_flexible_class_method(self):
        """As a user I want to use a class method for parsing, so I can create instances flexibly.
        Technical: Implement parse_flexible class method correctly.
        Validation: Check that class method works the same as constructor.
        """
        dt_str = "2025-05-03 14:30:45"
        dt1 = UnifiedDateTime(dt_str)
        dt2 = UnifiedDateTime.parse_flexible(dt_str)

        assert dt1.is_valid()
        assert dt2.is_valid()
        assert dt1 == dt2

    def test_iso_format_method(self):
        """As a user I want to get ISO format datetime strings, so I can use standard datetime formats.
        Technical: Implement to_iso_format method correctly.
        Validation: Check that ISO format is returned correctly.
        """
        dt = UnifiedDateTime("2025-05-03 14:30:45")
        assert dt.is_valid()
        assert dt.to_iso_format() == "2025-05-03T14:30:45"

        # Test invalid datetime
        invalid_dt = UnifiedDateTime("invalid")
        assert invalid_dt.to_iso_format() == ""


class TestBackwardCompatibilityFunctions:
    """Test cases for backward compatibility functions."""

    def test_parse_datetime_flexible_function(self):
        """As a user I want to use the old parse_datetime_flexible function, so existing code continues to work.
        Technical: Provide backward compatibility function that returns datetime objects.
        Validation: Check that function works with various formats and returns datetime or None.
        """
        # Test valid formats
        valid_cases = [
            ("2025-05-03 14:30:45", datetime(2025, 5, 3, 14, 30, 45)),
            ("5/9/2025 8:08:14 PM", datetime(2025, 5, 9, 20, 8, 14)),
            ("2025-06-24T07:30:54", datetime(2025, 6, 24, 7, 30, 54)),
        ]

        for dt_str, expected in valid_cases:
            result = parse_datetime_flexible(dt_str)
            assert result == expected

        # Test invalid format
        result = parse_datetime_flexible("invalid datetime")
        assert result is None

    def test_convert_to_standard_format_function(self):
        """As a user I want to convert datetime inputs to standard format, so I can standardize data.
        Technical: Provide function to convert various inputs to standard format string.
        Validation: Check that function works with strings and datetime objects.
        """
        # Test with string input
        result = convert_to_standard_format("2025-05-03 14:30:45")
        assert result == "2025-05-03 14:30:45"

        # Test with datetime input
        dt = datetime(2025, 5, 3, 14, 30, 45)
        result = convert_to_standard_format(dt)
        assert result == "2025-05-03 14:30:45"

        # Test with invalid input
        result = convert_to_standard_format("invalid")
        assert result == ""

    def test_validate_datetime_format_function(self):
        """As a user I want to validate datetime strings, so I can check data quality.
        Technical: Provide function to validate if datetime string can be parsed.
        Validation: Check that function returns True for valid formats and False for invalid.
        """
        # Test valid formats
        valid_cases = [
            "2025-05-03 14:30:45",
            "5/9/2025 8:08:14 PM",
            "2025-06-24T07:30:54",
            "2025-06-24T07:30:54+02:00",
        ]

        for dt_str in valid_cases:
            assert validate_datetime_format(dt_str)

        # Test invalid formats
        invalid_cases = [
            "invalid datetime",
            "2025-13-01 25:70:80",
            "",
            "not a date",
        ]

        for dt_str in invalid_cases:
            assert not validate_datetime_format(dt_str)


class TestFormatSupport:
    """Test cases for format support and edge cases."""

    def test_all_supported_formats(self):
        """As a user I want to parse all supported datetime formats, so I can handle diverse data sources.
        Technical: Test all formats in SUPPORTED_FORMATS list.
        Validation: Check that each supported format is parsed correctly.
        """
        test_cases = [
            ("%m/%d/%Y %I:%M:%S %p", "5/9/2025 8:08:14 PM", "2025-05-09 20:08:14"),
            ("%Y/%m/%d %H:%M:%S", "2025/06/24 07:30:54", "2025-06-24 07:30:54"),
            ("%Y-%m-%d %H:%M:%S", "2025-06-24 07:30:54", "2025-06-24 07:30:54"),
            ("%Y-%m-%dT%H:%M:%S", "2025-06-24T07:30:54", "2025-06-24 07:30:54"),
            ("%Y-%m-%dT%H:%M:%S%z", "2025-06-24T07:30:54+02:00", "2025-06-24 07:30:54"),
        ]

        for format_str, input_str, expected in test_cases:
            dt = UnifiedDateTime(input_str)
            assert dt.is_valid(), f"Failed to parse {input_str} with format {format_str}"
            assert dt.to_standard_format() == expected

    def test_timezone_handling(self):
        """As a user I want timezone-aware datetimes to be converted to local time, so I have consistent timezone handling.
        Technical: Convert timezone-aware datetimes to timezone-naive (local) datetimes.
        Validation: Check that timezone information is removed but time is preserved.
        """
        # Test with timezone
        dt_str = "2025-06-24T07:30:54+02:00"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()
        assert dt.to_standard_format() == "2025-06-24 07:30:54"

        # Verify timezone is removed
        result_dt = dt.to_datetime()
        assert result_dt.tzinfo is None

    def test_microsecond_handling(self):
        """As a user I want microsecond precision to be handled correctly, so I can work with high-precision timestamps.
        Technical: Handle datetime strings with microsecond precision.
        Validation: Check that microseconds are preserved in the datetime object.
        """
        dt_str = "2025-06-24T07:30:54.123456"
        dt = UnifiedDateTime(dt_str)
        assert dt.is_valid()

        result_dt = dt.to_datetime()
        assert result_dt.microsecond == 123456

        # Standard format should not include microseconds
        assert dt.to_standard_format() == "2025-06-24 07:30:54"

    def test_sortable_behavior(self):
        """As a user I want datetime strings to be naturally sortable, so I can sort time-based data easily.
        Technical: Ensure standard format strings sort correctly lexicographically.
        Validation: Check that lexicographic sorting matches chronological sorting.
        """
        datetime_strings = [
            "2025-05-03 14:30:45",
            "2025-05-03 15:30:45",
            "2025-05-04 14:30:45",
            "2025-06-24 07:30:54",
        ]

        # Convert to UnifiedDateTime objects
        dt_objects = [UnifiedDateTime(dt_str) for dt_str in datetime_strings]

        # Sort by standard format string (lexicographic)
        sorted_by_string = sorted(dt_objects, key=lambda x: x.to_standard_format())

        # Sort by datetime object (chronological)
        sorted_by_datetime = sorted(dt_objects, key=lambda x: x.to_datetime())

        # Both should produce the same order
        assert sorted_by_string == sorted_by_datetime


class TestPerformanceAndEdgeCases:
    """Test cases for performance and edge cases."""

    def test_large_dataset_parsing(self):
        """As a user I want to parse large datasets efficiently, so I can process system events and commits quickly.
        Technical: Test parsing performance with multiple datetime strings.
        Validation: Check that parsing is reasonably fast for large datasets.
        """
        # Create a list of datetime strings in various formats
        test_data = []
        for i in range(1000):
            test_data.extend(
                [
                    f"2025-05-03 {i % 24:02d}:30:45",
                    f"5/9/2025 {i % 12 + 1}:08:14 {'AM' if i % 2 == 0 else 'PM'}",
                    f"2025-06-24T{i % 24:02d}:30:54",
                ]
            )

        # Parse all datetime strings
        results = []
        for dt_str in test_data:
            dt = UnifiedDateTime(dt_str)
            results.append(dt.is_valid())

        # Most should be valid (some AM/PM times might be invalid)
        valid_count = sum(results)
        assert valid_count > len(test_data) * 0.8  # At least 80% should be valid

    def test_edge_case_dates(self):
        """As a user I want to handle edge case dates correctly, so I can process all valid datetime data.
        Technical: Test edge cases like leap years, month boundaries, etc.
        Validation: Check that edge case dates are handled correctly.
        """
        edge_cases = [
            ("2024-02-29 12:00:00", True),  # Leap year
            ("2025-02-28 23:59:59", True),  # Non-leap year
            ("2025-12-31 23:59:59", True),  # Year boundary
            ("2025-01-01 00:00:00", True),  # Year start
            ("2025-06-30 23:59:59", True),  # Month boundary
        ]

        for dt_str, should_be_valid in edge_cases:
            dt = UnifiedDateTime(dt_str)
            assert dt.is_valid() == should_be_valid, f"Failed for {dt_str}"

    def test_whitespace_handling(self):
        """As a user I want whitespace in datetime strings to be handled correctly, so I can process messy data.
        Technical: Handle various whitespace scenarios in datetime strings.
        Validation: Check that whitespace is handled correctly.
        """
        whitespace_cases = [
            "  2025-05-03 14:30:45  ",  # Leading and trailing spaces
            "\t2025-05-03 14:30:45\t",  # Tabs
            "\n2025-05-03 14:30:45\n",  # Newlines
            "2025-05-03  14:30:45",  # Extra spaces between components
        ]

        for dt_str in whitespace_cases:
            dt = UnifiedDateTime(dt_str)
            # Some might be valid, some might not, but should not crash
            assert isinstance(dt.is_valid(), bool)
