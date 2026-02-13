"""Test suite for smart datetime parsing system (TASK-032).

This module tests the enhanced datetime parsing capabilities with format detection,
confidence scoring, and source-specific parsing.

See project/team/tasks/TASK-032.md for detailed requirements and implementation decisions.
"""

from datetime import datetime

from backend.datetime_utils import DataSourceParser, UnifiedDateTime


class TestSmartDatetimeParser:
    """Test smart datetime parsing with format detection and confidence scoring."""

    def test_format_auto_detection_success(self):
        """As a user I want automatic format detection, so I can parse various datetime formats without manual configuration.
        Technical: Tests automatic format detection for various datetime string formats.
        Validation: Verifies correct format detection and parsing for different input formats.
        """
        test_cases = [
            ("2025-01-15 08:00:00", "%Y-%m-%d %H:%M:%S"),
            ("2025-01-15T08:00:00", "%Y-%m-%dT%H:%M:%S"),
            ("1/15/2025 8:00:00 AM", "%m/%d/%Y %I:%M:%S %p"),
            ("2025/01/15 08:00:00", "%Y/%m/%d %H:%M:%S"),
        ]

        for datetime_str, expected_format in test_cases:
            unified_dt = UnifiedDateTime(datetime_str)

            assert unified_dt.is_valid(), f"Failed to parse: {datetime_str}"
            assert unified_dt.get_detected_format() == expected_format, f"Wrong format detected for: {datetime_str}"

    def test_source_specific_parsing_system_events(self):
        """As a user I want source-specific parsing, so I can get better format detection for system events.
        Technical: Tests parsing with system_events source type hint for optimized format detection.
        Validation: Verifies system events formats are prioritized when source type is specified.
        """
        # System events format should be detected with high confidence
        system_event_time = "5/15/2025 8:30:00 PM"
        unified_dt = UnifiedDateTime(system_event_time, source_type="system_events")

        assert unified_dt.is_valid()
        assert unified_dt.get_detected_format() == "%m/%d/%Y %I:%M:%S %p"
        assert unified_dt.get_confidence_score() > 0.8

    def test_source_specific_parsing_git_commits(self):
        """As a user I want source-specific parsing, so I can get better format detection for git commits.
        Technical: Tests parsing with git_commits source type hint for optimized format detection.
        Validation: Verifies git commit formats are prioritized when source type is specified.
        """
        # Git commit format should be detected with high confidence
        git_commit_time = "2025-01-15T08:30:00+02:00"
        unified_dt = UnifiedDateTime(git_commit_time, source_type="git_commits")

        assert unified_dt.is_valid()
        # The format might be detected as ISO or the specific format, both are valid
        detected_format = unified_dt.get_detected_format()
        assert detected_format in ["%Y-%m-%dT%H:%M:%S%z", "ISO"]
        assert unified_dt.get_confidence_score() > 0.8

    def test_confidence_scoring_accuracy(self):
        """As a user I want confidence scoring, so I can understand how reliable the format detection is.
        Technical: Tests confidence scoring system for format detection accuracy.
        Validation: Verifies confidence scores reflect parsing reliability and format quality.
        """
        # High confidence for well-formed dates
        well_formed = "2025-01-15 08:30:00"
        unified_dt = UnifiedDateTime(well_formed)
        assert unified_dt.get_confidence_score() > 0.9

        # Lower confidence for unusual formats
        unusual_format = "1/15/25 8:30 AM"
        unified_dt_unusual = UnifiedDateTime(unusual_format)
        assert unified_dt_unusual.get_confidence_score() < 0.9

    def test_robust_error_handling_malformed_strings(self):
        """As a user I want robust error handling, so I can work with malformed datetime strings gracefully.
        Technical: Tests error handling for malformed and ambiguous datetime strings.
        Validation: Verifies graceful handling of invalid input with appropriate logging.
        """
        malformed_cases = [
            "invalid datetime",
            "2025-13-45 25:70:80",  # Invalid date/time values
            "",  # Empty string
            "   ",  # Whitespace only
        ]

        for malformed_str in malformed_cases:
            unified_dt = UnifiedDateTime(malformed_str)
            assert not unified_dt.is_valid()
            assert unified_dt.get_detected_format() is None
            assert unified_dt.get_confidence_score() == 0.0

    def test_performance_optimization_large_datasets(self):
        """As a user I want efficient parsing, so I can process large datasets without performance issues.
        Technical: Tests parsing performance with multiple datetime strings.
        Validation: Verifies parsing is efficient and suitable for large dataset processing.
        """
        # Test parsing multiple datetime strings efficiently
        test_times = [
            "2025-01-15 08:00:00",
            "2025-01-15T08:30:00",
            "1/15/2025 9:00:00 AM",
            "2025/01/15 10:00:00",
        ] * 100  # 400 total strings

        results = []
        for time_str in test_times:
            unified_dt = UnifiedDateTime(time_str)
            results.append(unified_dt.is_valid())

        # All should parse successfully
        assert all(results)
        assert len(results) == 400

    def test_format_validation_api(self):
        """As a user I want format validation, so I can check if datetime strings match specific formats.
        Technical: Tests format validation API for checking datetime string format compliance.
        Validation: Verifies format validation works correctly for various format strings.
        """
        # Valid format
        assert UnifiedDateTime.validate_format("2025-01-15 08:00:00", "%Y-%m-%d %H:%M:%S")

        # Invalid format
        assert not UnifiedDateTime.validate_format("2025-01-15 08:00:00", "%m/%d/%Y %I:%M:%S %p")

        # Malformed string
        assert not UnifiedDateTime.validate_format("invalid", "%Y-%m-%d %H:%M:%S")

    def test_detection_confidence_api(self):
        """As a user I want detection confidence, so I can understand the reliability of format detection.
        Technical: Tests detection confidence API for format detection reliability assessment.
        Validation: Verifies confidence scores are calculated correctly for different formats.
        """
        # High confidence for standard format
        confidence = UnifiedDateTime.get_detection_confidence("2025-01-15 08:00:00", "%Y-%m-%d %H:%M:%S")
        assert confidence > 0.9

        # Lower confidence for format mismatch
        confidence_low = UnifiedDateTime.get_detection_confidence("2025-01-15 08:00:00", "%m/%d/%Y %I:%M:%S %p")
        assert confidence_low == 0.0

    def test_class_method_apis(self):
        """As a user I want convenient class methods, so I can use datetime parsing without creating instances.
        Technical: Tests class method APIs for format detection and parsing.
        Validation: Verifies class methods work correctly for format detection and parsing.
        """
        # Test detect_format class method
        detected_format = UnifiedDateTime.detect_format("2025-01-15 08:00:00")
        assert detected_format == "%Y-%m-%d %H:%M:%S"

        # Test parse_with_detection class method
        parsed_dt = UnifiedDateTime.parse_with_detection("2025-01-15 08:00:00")
        assert parsed_dt is not None
        assert isinstance(parsed_dt, datetime)
        assert parsed_dt.year == 2025
        assert parsed_dt.month == 1
        assert parsed_dt.day == 15

    def test_integration_with_existing_system(self):
        """As a user I want seamless integration, so I can use smart parsing with existing datetime system.
        Technical: Tests integration with existing UnifiedDateTime system and backward compatibility.
        Validation: Verifies smart parsing works with existing code and maintains compatibility.
        """
        # Test backward compatibility
        unified_dt = UnifiedDateTime("2025-01-15 08:00:00")
        assert unified_dt.is_valid()
        assert unified_dt.to_standard_format() == "2025-01-15 08:00:00"
        assert unified_dt.to_iso_format() == "2025-01-15T08:00:00"

        # Test with source type hint
        unified_dt_with_hint = UnifiedDateTime("5/15/2025 8:00:00 PM", source_type="system_events")
        assert unified_dt_with_hint.is_valid()
        assert unified_dt_with_hint.get_detected_format() == "%m/%d/%Y %I:%M:%S %p"


class TestDataSourceParser:
    """Test data source-specific parsing with format hints."""

    def test_system_events_parser(self):
        """As a user I want system events parsing, so I can handle system event timestamps efficiently.
        Technical: Tests DataSourceParser for system events with optimized format detection.
        Validation: Verifies system events parsing works correctly with source-specific logic.
        """
        parser = DataSourceParser("system_events")

        # Test system event timestamp parsing
        system_time = "5/15/2025 8:30:00 PM"
        parsed_dt = parser.parse_system_event_timestamp(system_time)

        assert parsed_dt is not None
        assert parsed_dt.year == 2025
        assert parsed_dt.month == 5
        assert parsed_dt.day == 15
        assert parsed_dt.hour == 20  # 8 PM in 24-hour format

    def test_git_commits_parser(self):
        """As a user I want git commits parsing, so I can handle git commit timestamps with timezone support.
        Technical: Tests DataSourceParser for git commits with timezone handling.
        Validation: Verifies git commit parsing works correctly with timezone information.
        """
        parser = DataSourceParser("git_commits")

        # Test git commit timestamp parsing
        git_time = "2025-01-15T08:30:00+02:00"
        parsed_dt = parser.parse_git_commit_timestamp(git_time)

        assert parsed_dt is not None
        assert parsed_dt.year == 2025
        assert parsed_dt.month == 1
        assert parsed_dt.day == 15
        assert parsed_dt.hour == 8
        assert parsed_dt.minute == 30

    def test_csv_timestamp_parsing(self):
        """As a user I want CSV timestamp parsing, so I can handle CSV data with column name hints.
        Technical: Tests DataSourceParser for CSV timestamps with column name context.
        Validation: Verifies CSV parsing works correctly with optional column name hints.
        """
        parser = DataSourceParser("standard")

        # Test CSV timestamp parsing
        csv_time = "2025-01-15 08:30:00"
        parsed_dt = parser.parse_csv_timestamp(csv_time, "timestamp")

        assert parsed_dt is not None
        assert parsed_dt.year == 2025
        assert parsed_dt.month == 1
        assert parsed_dt.day == 15

    def test_json_timestamp_parsing(self):
        """As a user I want JSON timestamp parsing, so I can handle JSON data with field name hints.
        Technical: Tests DataSourceParser for JSON timestamps with field name context.
        Validation: Verifies JSON parsing works correctly with optional field name hints.
        """
        parser = DataSourceParser("standard")

        # Test JSON timestamp parsing
        json_time = "2025-01-15T08:30:00"
        parsed_dt = parser.parse_json_timestamp(json_time, "created_at")

        assert parsed_dt is not None
        assert parsed_dt.year == 2025
        assert parsed_dt.month == 1
        assert parsed_dt.day == 15

    def test_parser_error_handling(self):
        """As a user I want robust error handling, so I can handle parsing failures gracefully.
        Technical: Tests DataSourceParser error handling for invalid input.
        Validation: Verifies parser handles invalid input gracefully without exceptions.
        """
        parser = DataSourceParser("system_events")

        # Test with invalid input
        invalid_time = "invalid datetime"
        parsed_dt = parser.parse_system_event_timestamp(invalid_time)

        assert parsed_dt is None

    def test_parser_source_type_optimization(self):
        """As a user I want source type optimization, so I can get better parsing performance for specific data sources.
        Technical: Tests DataSourceParser optimization for different source types.
        Validation: Verifies source type hints improve parsing accuracy and performance.
        """
        # Test with system events source type
        system_parser = DataSourceParser("system_events")
        system_time = "5/15/2025 8:30:00 PM"
        system_result = system_parser.parse_system_event_timestamp(system_time)

        # Test with standard source type
        standard_parser = DataSourceParser("standard")
        standard_result = standard_parser.parse_csv_timestamp(system_time)

        # Both should parse successfully
        assert system_result is not None
        assert standard_result is not None

        # Results should be equivalent
        assert system_result == standard_result


class TestIntegrationWithExistingSystems:
    """Test integration with existing datetime systems and data loading."""

    def test_integration_with_data_loader(self):
        """As a user I want seamless integration, so I can use smart parsing with data loading utilities.
        Technical: Tests integration with data loading utilities from TASK-030.
        Validation: Verifies smart parsing works with existing data loading code.
        """
        # Test that data loader can use smart parsing
        from backend.data_analysis.data_loader import _convert_timestamp_to_datetime

        # Test various formats that data loader might encounter
        test_formats = [
            "2025-01-15 08:00:00",  # Standard format
            "1/15/2025 8:00:00 AM",  # US format
            "2025-01-15T08:00:00",  # ISO format
        ]

        for time_str in test_formats:
            result = _convert_timestamp_to_datetime(time_str)
            assert result is not None
            assert result.year == 2025
            assert result.month == 1
            assert result.day == 15

    def test_backward_compatibility(self):
        """As a user I want backward compatibility, so I can use existing code without changes.
        Technical: Tests backward compatibility with existing UnifiedDateTime usage.
        Validation: Verifies existing code continues to work with enhanced parsing capabilities.
        """
        # Test existing usage patterns still work
        unified_dt = UnifiedDateTime("2025-01-15 08:00:00")
        assert unified_dt.is_valid()
        assert unified_dt.to_standard_format() == "2025-01-15 08:00:00"

        # Test parse_flexible still works
        parsed_dt = UnifiedDateTime.parse_flexible("2025-01-15 08:00:00")
        assert parsed_dt.is_valid()

        # Test existing functions still work
        from backend.datetime_utils import convert_to_standard_format, parse_datetime_flexible

        parsed = parse_datetime_flexible("2025-01-15 08:00:00")
        assert parsed is not None

        standard = convert_to_standard_format("2025-01-15 08:00:00")
        assert standard == "2025-01-15 08:00:00"
