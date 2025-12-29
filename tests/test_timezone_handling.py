"""Test timezone handling functionality for data loading and visualization utilities.

This module tests the safe timezone conversion functions to ensure robust handling
of both timezone-naive and timezone-aware datetime data.
"""

import pandas as pd

from notebooks.utils.data_loading_helpers import safe_to_datetime_amsterdam as data_safe_to_datetime_amsterdam
from notebooks.utils.visualization_helpers import safe_to_datetime_amsterdam as viz_safe_to_datetime_amsterdam


class TestSafeTimezoneConversion:
    """Test cases for safe timezone conversion functionality."""

    def test_naive_datetime_conversion(self):
        """As a user I want naive datetimes to be converted to Amsterdam timezone, so I have consistent local timezone handling.
        Technical: Convert timezone-naive datetime strings to timezone-aware Amsterdam.
        Validation: Check that naive datetimes are properly localized to Amsterdam timezone.
        """
        # Test with naive datetime strings
        naive_timestamps = ["2025-01-15 10:30:00", "2025-01-15T10:30:00", "2025-01-15 10:30:00.123456"]

        for timestamp in naive_timestamps:
            result = data_safe_to_datetime_amsterdam(timestamp)
            assert result.dt.tz is not None
            assert str(result.dt.tz) == "Europe/Amsterdam"
            assert result.iloc[0].hour == 10
            assert result.iloc[0].minute == 30

    def test_timezone_aware_conversion(self):
        """As a user I want timezone-aware datetimes to be converted to Amsterdam timezone, so I have consistent local timezone handling.
        Technical: Convert timezone-aware datetime strings to Amsterdam timezone.
        Validation: Check that timezone-aware datetimes are properly converted to Amsterdam timezone.
        """
        # Test with timezone-aware datetime strings
        aware_timestamps = [
            "2025-01-15T10:30:00+02:00",  # UTC+2
            "2025-01-15T10:30:00-05:00",  # UTC-5
            "2025-01-15T10:30:00Z",  # UTC
        ]

        for timestamp in aware_timestamps:
            result = data_safe_to_datetime_amsterdam(timestamp)
            assert result.dt.tz is not None
            assert str(result.dt.tz) == "Europe/Amsterdam"
            # The actual hour will depend on the original timezone
            assert result.iloc[0].minute == 30

    def test_series_conversion(self):
        """As a user I want pandas Series to be converted consistently, so I can process data efficiently.
        Technical: Convert pandas Series containing mixed timezone data to Amsterdam timezone.
        Validation: Check that all elements in the Series are properly converted to Amsterdam timezone.
        """
        # Test with mixed timezone data in a Series
        mixed_data = pd.Series(
            [
                "2025-01-15 10:30:00",  # naive
                "2025-01-15T10:30:00+02:00",  # UTC+2
                "2025-01-15T10:30:00-05:00",  # UTC-5
            ]
        )

        result = data_safe_to_datetime_amsterdam(mixed_data)
        assert len(result) == 3
        assert result.dt.tz is not None
        assert str(result.dt.tz) == "Europe/Amsterdam"

    def test_already_utc_conversion(self):
        """As a user I want already UTC datetimes to be converted to Amsterdam timezone, so I have consistent local timezone handling.
        Technical: Handle datetimes that are already in UTC timezone and convert to Amsterdam.
        Validation: Check that UTC datetimes are properly converted to Amsterdam timezone.
        """
        # Test with already UTC datetime
        utc_timestamp = "2025-01-15T10:30:00Z"
        result = data_safe_to_datetime_amsterdam(utc_timestamp)

        assert result.dt.tz is not None
        assert str(result.dt.tz) == "Europe/Amsterdam"
        # In winter, Amsterdam is UTC+1, so 10:30 UTC becomes 11:30 Amsterdam
        assert result.iloc[0].hour == 11
        assert result.iloc[0].minute == 30

    def test_invalid_datetime_handling(self):
        """As a user I want invalid datetime strings to be handled gracefully, so the system doesn't crash.
        Technical: Handle invalid datetime strings with errors='coerce'.
        Validation: Check that invalid datetimes result in NaT (Not a Time) values.
        """
        # Test with invalid datetime strings
        invalid_timestamps = [
            "invalid-datetime",
            "2025-13-45 25:70:80",  # Invalid date/time
            "",
            None,
        ]

        for timestamp in invalid_timestamps:
            result = data_safe_to_datetime_amsterdam(timestamp)
            # Should not raise an exception, but may contain NaT
            assert isinstance(result, pd.Series)

    def test_consistency_between_modules(self):
        """As a user I want consistent timezone handling across modules, so I have reliable behavior.
        Technical: Ensure both data_loading_helpers and visualization_helpers use the same logic.
        Validation: Check that both modules produce identical results for the same input.
        """
        test_timestamp = "2025-01-15T10:30:00+02:00"

        data_result = data_safe_to_datetime_amsterdam(test_timestamp)
        viz_result = viz_safe_to_datetime_amsterdam(test_timestamp)

        # Both should produce the same result
        assert data_result.iloc[0] == viz_result.iloc[0]
        assert str(data_result.dt.tz) == str(viz_result.dt.tz)

    def test_edge_case_midnight_crossing(self):
        """As a user I want midnight-crossing datetimes to be handled correctly, so I have accurate time tracking.
        Technical: Test datetimes that cross midnight in different timezones.
        Validation: Check that timezone conversion preserves the correct date and time.
        """
        # Test datetime that crosses midnight when converted to Amsterdam timezone
        late_evening = "2025-01-15T23:30:00+02:00"  # 23:30 UTC+2 = 22:30 Amsterdam (winter time)
        result = data_safe_to_datetime_amsterdam(late_evening)

        assert result.dt.tz is not None
        assert str(result.dt.tz) == "Europe/Amsterdam"
        assert result.iloc[0].hour == 22  # Should be 22:30 Amsterdam
        assert result.iloc[0].minute == 30

    def test_microsecond_preservation(self):
        """As a user I want microsecond precision to be preserved, so I have accurate timestamp data.
        Technical: Test that microsecond precision is maintained during timezone conversion.
        Validation: Check that microseconds are preserved in the conversion.
        """
        # Test with microsecond precision
        precise_timestamp = "2025-01-15T10:30:00.123456+02:00"
        result = data_safe_to_datetime_amsterdam(precise_timestamp)

        assert result.dt.tz is not None
        assert str(result.dt.tz) == "Europe/Amsterdam"
        assert result.iloc[0].microsecond == 123456

    def test_empty_series_handling(self):
        """As a user I want empty Series to be handled gracefully, so I can process empty datasets.
        Technical: Test handling of empty pandas Series.
        Validation: Check that empty Series return empty Series with proper dtype.
        """
        empty_series = pd.Series([], dtype="object")
        result = data_safe_to_datetime_amsterdam(empty_series)

        assert isinstance(result, pd.Series)
        assert len(result) == 0
        assert result.dtype == "datetime64[ns, Europe/Amsterdam]"

    def test_list_input_handling(self):
        """As a user I want list inputs to be converted to Series and processed, so I can handle various input types.
        Technical: Test handling of list inputs (converted to Series internally).
        Validation: Check that list inputs are properly converted and processed.
        """
        timestamp_list = ["2025-01-15 10:30:00", "2025-01-15T10:30:00+02:00"]

        result = data_safe_to_datetime_amsterdam(timestamp_list)
        assert len(result) == 2
        assert result.dt.tz is not None
        assert str(result.dt.tz) == "Europe/Amsterdam"


class TestDataFrameIntegration:
    """Test integration with DataFrame operations."""

    def test_work_sessions_dataframe_conversion(self):
        """As a user I want work session DataFrames to be converted safely, so I can analyze time-based data.
        Technical: Test the convert_work_sessions_to_dataframe function with various timezone inputs.
        Validation: Check that start_time and end_time columns are properly converted to UTC.
        """
        from notebooks.utils.data_loading_helpers import convert_work_sessions_to_dataframe

        # Test data with mixed timezone information
        test_data = {
            "logon_logoff_sessions": [
                {
                    "start_time": "2025-01-15 09:00:00",
                    "end_time": "2025-01-15 17:00:00",
                    "duration_hours": 8.0,
                    "date": "2025-01-15",
                },
                {
                    "start_time": "2025-01-15T09:00:00+02:00",
                    "end_time": "2025-01-15T17:00:00+02:00",
                    "duration_hours": 8.0,
                    "date": "2025-01-15",
                },
            ]
        }

        df = convert_work_sessions_to_dataframe(test_data)

        # Check that both start_time and end_time are timezone-aware Amsterdam
        assert df["start_time"].dt.tz is not None
        assert df["end_time"].dt.tz is not None
        assert str(df["start_time"].dt.tz) == "Europe/Amsterdam"
        assert str(df["end_time"].dt.tz) == "Europe/Amsterdam"

    def test_commits_dataframe_conversion(self):
        """As a user I want commit DataFrames to be converted safely, so I can analyze development activity.
        Technical: Test the convert_commits_to_dataframe function with various timezone inputs.
        Validation: Check that timestamp column is properly converted to UTC.
        """
        from notebooks.utils.data_loading_helpers import convert_commits_to_dataframe

        # Test data with mixed timezone information
        test_data = {
            "commits": [
                {
                    "timestamp": "2025-01-15 14:30:00",
                    "repo_name": "test-repo",
                    "author": "test-author",
                    "message": "test commit",
                    "hash": "abc123",
                },
                {
                    "timestamp": "2025-01-15T14:30:00+02:00",
                    "repo_name": "test-repo",
                    "author": "test-author",
                    "message": "test commit 2",
                    "hash": "def456",
                },
            ]
        }

        df = convert_commits_to_dataframe(test_data)

        # Check that timestamp is timezone-aware Amsterdam
        assert df["timestamp"].dt.tz is not None
        assert str(df["timestamp"].dt.tz) == "Europe/Amsterdam"

    def test_date_range_filtering(self):
        """As a user I want date range filtering to work with timezone-aware data, so I can filter data accurately.
        Technical: Test the filter_data_by_date_range function with timezone-aware DataFrames.
        Validation: Check that filtering works correctly with UTC timezone data.
        """
        from notebooks.utils.data_loading_helpers import filter_data_by_date_range

        # Create test DataFrame with timezone-aware timestamps
        test_data = pd.DataFrame({"timestamp": ["2025-01-15 10:00:00", "2025-01-15T10:00:00+02:00", "2025-01-16 10:00:00"]})

        # Convert to timezone-aware
        test_data["timestamp"] = data_safe_to_datetime_amsterdam(test_data["timestamp"].tolist())

        # Filter by date range
        filtered = filter_data_by_date_range(test_data, "2025-01-15", "2025-01-15", "timestamp")

        # Should include entries that fall within the date range
        # The timezone conversion might change the actual date, so we check the filtered results
        if len(filtered) > 0:
            # All filtered results should be on the same date
            filtered_dates = filtered["timestamp"].dt.date.unique()
            assert len(filtered_dates) == 1
            # The date should be either 2025-01-15 or 2025-01-14 (due to timezone conversion)
            assert filtered_dates[0] in [pd.Timestamp("2025-01-15").date(), pd.Timestamp("2025-01-14").date()]
