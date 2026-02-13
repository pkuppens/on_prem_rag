"""Comprehensive test suite for pandas-based data analysis functionality.

This module tests the data loading utilities and time series analysis framework
implemented in TASK-030 for work session tracking and commit correlation.

See project/team/tasks/TASK-030.md for detailed requirements and implementation decisions.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from backend.data_analysis import (
    TimeSeriesAnalyzer,
    load_commits_data,
    load_system_events_data,
    prepare_time_series_data,
)
from backend.datetime_utils import UnifiedDateTime


class TestDataLoader:
    """Test data loading utilities for CSV and JSON files."""

    def test_load_system_events_data_success(self):
        """As a user I want to load system events from CSV files, so I can analyze work patterns.
        Technical: Tests successful loading of system events CSV files with proper data types and formatting.
        Validation: Verifies DataFrame structure, column names, and data integrity.
        """
        # Create temporary CSV file with system events data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = temp_path / "system_events.csv"

            # Create test data
            test_data = [
                {"TimeGenerated": "2025-01-15 08:00:00", "EventType": "startup", "EventID": 6005, "ComputerName": "WORKSTATION-01"},
                {
                    "TimeGenerated": "2025-01-15 17:30:00",
                    "EventType": "shutdown",
                    "EventID": 1074,
                    "ComputerName": "WORKSTATION-01",
                },
            ]

            df_test = pd.DataFrame(test_data)
            df_test.to_csv(csv_file, index=False)

            # Load data
            result_df = load_system_events_data(temp_path)

            # Verify structure
            assert len(result_df) == 2
            assert list(result_df.columns) == ["timestamp", "event_type", "event_id", "computer_name"]
            assert result_df["event_type"].tolist() == ["startup", "shutdown"]
            assert result_df["computer_name"].tolist() == ["WORKSTATION-01", "WORKSTATION-01"]

            # Verify timestamp conversion
            assert isinstance(result_df["timestamp"].iloc[0], pd.Timestamp)
            assert result_df["timestamp"].iloc[0].hour == 8
            assert result_df["timestamp"].iloc[1].hour == 17

    def test_load_system_events_data_multiple_files(self):
        """As a user I want to load multiple CSV files, so I can combine data from different sources.
        Technical: Tests loading and combining multiple CSV files into a single DataFrame.
        Validation: Verifies data is properly combined and sorted by timestamp.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple CSV files
            for i, (hour, event_type) in enumerate([(8, "startup"), (17, "shutdown")]):
                csv_file = temp_path / f"events_{i}.csv"
                test_data = [
                    {
                        "TimeGenerated": f"2025-01-15 {hour:02d}:00:00",
                        "EventType": event_type,
                        "EventID": 6005 + i,
                        "ComputerName": f"WORKSTATION-{i + 1:02d}",
                    }
                ]
                pd.DataFrame(test_data).to_csv(csv_file, index=False)

            # Load data
            result_df = load_system_events_data(temp_path)

            # Verify combined data
            assert len(result_df) == 2
            assert result_df["computer_name"].nunique() == 2
            assert result_df["timestamp"].is_monotonic_increasing

    def test_load_system_events_data_missing_directory(self):
        """As a user I want proper error handling, so I can understand when data loading fails.
        Technical: Tests error handling for missing data directory.
        Validation: Verifies FileNotFoundError is raised for non-existent directory.
        """
        with pytest.raises(FileNotFoundError):
            load_system_events_data(Path("/non/existent/directory"))

    def test_load_system_events_data_no_csv_files(self):
        """As a user I want proper error handling, so I can understand when no data is found.
        Technical: Tests error handling for directory with no CSV files.
        Validation: Verifies ValueError is raised when no CSV files are found.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a non-CSV file
            (temp_path / "not_a_csv.txt").write_text("not csv data")

            with pytest.raises(ValueError, match="No CSV files found"):
                load_system_events_data(temp_path)

    def test_load_commits_data_success(self):
        """As a user I want to load commit data from JSON files, so I can analyze development patterns.
        Technical: Tests successful loading of commits JSON file with proper data types and formatting.
        Validation: Verifies DataFrame structure, column names, and data integrity.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_file = temp_path / "commits.json"

            # Create test data
            test_data = [
                {
                    "commit_time": "2025-01-15 10:30:00",
                    "repository": "on_prem_rag",
                    "author": "Pieter Kuppens",
                    "commit_message": "Fix authentication bug",
                    "wbso_eligible": True,
                },
                {
                    "commit_time": "2025-01-15 14:15:00",
                    "repository": "on_prem_rag",
                    "author": "Pieter Kuppens",
                    "commit_message": "Add new feature",
                    "wbso_eligible": True,
                },
            ]

            with open(json_file, "w") as f:
                json.dump(test_data, f)

            # Load data
            result_df = load_commits_data(json_file)

            # Verify structure
            assert len(result_df) == 2
            assert list(result_df.columns) == ["timestamp", "repo_name", "author", "message", "is_wbso"]
            assert result_df["author"].tolist() == ["Pieter Kuppens", "Pieter Kuppens"]
            assert result_df["is_wbso"].all()

            # Verify timestamp conversion
            assert isinstance(result_df["timestamp"].iloc[0], pd.Timestamp)
            assert result_df["timestamp"].iloc[0].hour == 10

    def test_load_commits_data_missing_file(self):
        """As a user I want proper error handling, so I can understand when commit data loading fails.
        Technical: Tests error handling for missing commits file.
        Validation: Verifies FileNotFoundError is raised for non-existent file.
        """
        with pytest.raises(FileNotFoundError):
            load_commits_data(Path("/non/existent/commits.json"))

    def test_load_commits_data_invalid_json(self):
        """As a user I want proper error handling, so I can understand when JSON data is invalid.
        Technical: Tests error handling for invalid JSON format.
        Validation: Verifies ValueError is raised for malformed JSON.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_file = temp_path / "invalid.json"

            # Write invalid JSON
            json_file.write_text("{ invalid json }")

            with pytest.raises(ValueError, match="Invalid JSON"):
                load_commits_data(json_file)

    def test_prepare_time_series_data_success(self):
        """As a user I want to prepare data for time series analysis, so I can perform efficient time-based operations.
        Technical: Tests preparation of DataFrames with datetime indexing for time series analysis.
        Validation: Verifies proper datetime indexing and data sorting.
        """
        # Create test DataFrames
        system_events_df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2025-01-15 08:00:00", "2025-01-15 17:30:00"]),
                "event_type": ["startup", "shutdown"],
                "event_id": [6005, 1074],
                "computer_name": ["WORKSTATION-01", "WORKSTATION-01"],
            }
        )

        commits_df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2025-01-15 10:30:00", "2025-01-15 14:15:00"]),
                "repo_name": ["on_prem_rag", "on_prem_rag"],
                "author": ["Pieter Kuppens", "Pieter Kuppens"],
                "message": ["Fix bug", "Add feature"],
                "is_wbso": [True, True],
            }
        )

        # Prepare data
        prepared_system, prepared_commits = prepare_time_series_data(system_events_df, commits_df)

        # Verify system events preparation
        assert isinstance(prepared_system.index, pd.DatetimeIndex)
        assert prepared_system.index.is_monotonic_increasing
        assert "timestamp" not in prepared_system.columns  # Should be moved to index

        # Verify commits preparation
        assert isinstance(prepared_commits.index, pd.DatetimeIndex)
        assert prepared_commits.index.is_monotonic_increasing
        assert "timestamp" not in prepared_commits.columns  # Should be moved to index

    def test_prepare_time_series_data_empty_dataframes(self):
        """As a user I want to handle empty data gracefully, so I can work with incomplete datasets.
        Technical: Tests preparation of empty DataFrames for time series analysis.
        Validation: Verifies empty DataFrames are handled without errors.
        """
        empty_df = pd.DataFrame()
        prepared_system, prepared_commits = prepare_time_series_data(empty_df, empty_df)

        assert prepared_system.empty
        assert prepared_commits.empty


class TestTimeSeriesAnalyzer:
    """Test time series analysis framework for work session data."""

    @pytest.fixture
    def sample_system_events_df(self) -> pd.DataFrame:
        """Create sample system events DataFrame for testing."""
        data = [
            {"timestamp": "2025-01-15 08:00:00", "event_type": "startup", "event_id": 6005, "computer_name": "WORKSTATION-01"},
            {"timestamp": "2025-01-15 12:00:00", "event_type": "activity", "event_id": 1000, "computer_name": "WORKSTATION-01"},
            {"timestamp": "2025-01-15 17:30:00", "event_type": "shutdown", "event_id": 1074, "computer_name": "WORKSTATION-01"},
            {"timestamp": "2025-01-16 09:00:00", "event_type": "startup", "event_id": 6005, "computer_name": "WORKSTATION-02"},
            {"timestamp": "2025-01-16 18:00:00", "event_type": "shutdown", "event_id": 1074, "computer_name": "WORKSTATION-02"},
        ]
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        return df

    @pytest.fixture
    def sample_commits_df(self) -> pd.DataFrame:
        """Create sample commits DataFrame for testing."""
        data = [
            {
                "timestamp": "2025-01-15 10:30:00",
                "repo_name": "on_prem_rag",
                "author": "Pieter Kuppens",
                "message": "Fix bug",
                "is_wbso": True,
            },
            {
                "timestamp": "2025-01-15 14:15:00",
                "repo_name": "on_prem_rag",
                "author": "Pieter Kuppens",
                "message": "Add feature",
                "is_wbso": True,
            },
            {
                "timestamp": "2025-01-16 11:00:00",
                "repo_name": "on_prem_rag",
                "author": "Pieter Kuppens",
                "message": "Update docs",
                "is_wbso": False,
            },
        ]
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        return df

    def test_analyzer_initialization_success(self, sample_system_events_df, sample_commits_df):
        """As a user I want to initialize the analyzer with my data, so I can perform time series analysis.
        Technical: Tests successful initialization of TimeSeriesAnalyzer with valid DataFrames.
        Validation: Verifies analyzer is properly initialized with computed columns.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        # Verify computed columns are added
        assert "is_startup" in analyzer.system_events_df.columns
        assert "is_shutdown" in analyzer.system_events_df.columns
        assert "hour" in analyzer.system_events_df.columns
        assert "day_of_week" in analyzer.system_events_df.columns

        assert "hour" in analyzer.commits_df.columns
        assert "day_of_week" in analyzer.commits_df.columns
        assert "message_length" in analyzer.commits_df.columns

    def test_analyzer_initialization_invalid_dataframes(self):
        """As a user I want proper error handling, so I can understand when analyzer initialization fails.
        Technical: Tests error handling for invalid DataFrame structures.
        Validation: Verifies ValueError is raised for DataFrames without datetime index.
        """
        # Test with DataFrame without datetime index
        invalid_df = pd.DataFrame({"event_type": ["startup"], "event_id": [6005]})

        with pytest.raises(ValueError, match="must have datetime index"):
            TimeSeriesAnalyzer(invalid_df, pd.DataFrame())

    def test_filter_by_time_range_success(self, sample_system_events_df, sample_commits_df):
        """As a user I want to filter data by time range, so I can focus on specific periods.
        Technical: Tests time range filtering with various time string formats.
        Validation: Verifies filtering works correctly and returns appropriate data subsets.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        # Filter by time range
        filtered_system, filtered_commits = analyzer.filter_by_time_range("2025-01-15 09:00:00", "2025-01-15 16:00:00")

        # Verify filtering results
        assert len(filtered_system) == 1  # only activity event in range
        assert len(filtered_commits) == 2  # both commits on 2025-01-15

        # Verify all filtered events are within time range
        assert filtered_system.index.min() >= pd.Timestamp("2025-01-15 09:00:00")
        assert filtered_system.index.max() <= pd.Timestamp("2025-01-15 16:00:00")

    def test_filter_by_time_range_invalid_times(self, sample_system_events_df, sample_commits_df):
        """As a user I want proper error handling, so I can understand when time filtering fails.
        Technical: Tests error handling for invalid time string formats.
        Validation: Verifies ValueError is raised for unparseable time strings.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        with pytest.raises(ValueError, match="Invalid time format"):
            analyzer.filter_by_time_range("invalid-time", "2025-01-15 16:00:00")

    def test_aggregate_by_period_success(self, sample_system_events_df, sample_commits_df):
        """As a user I want to aggregate data by time periods, so I can analyze patterns and trends.
        Technical: Tests data aggregation by different time periods (hour, day, week, month).
        Validation: Verifies aggregation produces correct statistics and handles empty periods.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        # Test daily aggregation
        daily_agg = analyzer.aggregate_by_period("D")

        assert len(daily_agg) == 2  # Two days of data
        assert "system_events_count" in daily_agg.columns
        assert "commits_count" in daily_agg.columns
        assert "wbso_commits" in daily_agg.columns

        # Verify aggregation values
        assert daily_agg["system_events_count"].sum() == len(sample_system_events_df)
        assert daily_agg["commits_count"].sum() == len(sample_commits_df)

    def test_aggregate_by_period_invalid_period(self, sample_system_events_df, sample_commits_df):
        """As a user I want proper error handling, so I can understand when aggregation fails.
        Technical: Tests error handling for invalid aggregation periods.
        Validation: Verifies ValueError is raised for unsupported period values.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        with pytest.raises(ValueError, match="Period must be one of"):
            analyzer.aggregate_by_period("invalid")

    def test_detect_work_sessions_success(self, sample_system_events_df, sample_commits_df):
        """As a user I want to detect work sessions from system events, so I can understand my work patterns.
        Technical: Tests work session detection based on startup/shutdown patterns.
        Validation: Verifies sessions are correctly identified with proper start/end times.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        sessions_df = analyzer.detect_work_sessions()

        # Verify session detection
        assert len(sessions_df) == 2  # Two work sessions (one per computer)
        assert "session_start" in sessions_df.columns
        assert "session_end" in sessions_df.columns
        assert "duration_minutes" in sessions_df.columns
        assert "computer_name" in sessions_df.columns

        # Verify session times
        assert sessions_df["session_start"].iloc[0] == pd.Timestamp("2025-01-15 08:00:00")
        assert sessions_df["session_end"].iloc[0] == pd.Timestamp("2025-01-15 17:30:00")

    def test_detect_work_sessions_empty_data(self):
        """As a user I want to handle empty data gracefully, so I can work with incomplete datasets.
        Technical: Tests work session detection with empty system events data.
        Validation: Verifies empty DataFrame is returned when no system events are available.
        """
        analyzer = TimeSeriesAnalyzer(pd.DataFrame(), pd.DataFrame())

        sessions_df = analyzer.detect_work_sessions()

        assert sessions_df.empty
        assert list(sessions_df.columns) == ["session_start", "session_end", "duration_minutes", "computer_name"]

    def test_correlate_commits_with_sessions_success(self, sample_system_events_df, sample_commits_df):
        """As a user I want to correlate commits with work sessions, so I can understand which commits were made during active work.
        Technical: Tests commit-session correlation using time-based overlap analysis.
        Validation: Verifies commits are correctly matched to overlapping work sessions.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        correlated_df = analyzer.correlate_commits_with_sessions()

        # Verify correlation results
        assert len(correlated_df) == len(sample_commits_df)
        assert "session_id" in correlated_df.columns
        assert "session_duration_minutes" in correlated_df.columns

        # Verify commits are correlated with sessions
        commits_in_sessions = correlated_df[correlated_df["session_id"].notna()]
        assert len(commits_in_sessions) > 0  # At least some commits should be in sessions

    def test_correlate_commits_with_sessions_empty_data(self):
        """As a user I want to handle empty data gracefully, so I can work with incomplete datasets.
        Technical: Tests commit-session correlation with empty commits data.
        Validation: Verifies empty DataFrame is returned when no commits are available.
        """
        analyzer = TimeSeriesAnalyzer(pd.DataFrame(), pd.DataFrame())

        correlated_df = analyzer.correlate_commits_with_sessions()

        assert correlated_df.empty

    def test_get_work_patterns_summary_success(self, sample_system_events_df, sample_commits_df):
        """As a user I want to get a summary of my work patterns, so I can understand my productivity and work habits.
        Technical: Tests generation of comprehensive work pattern statistics and insights.
        Validation: Verifies summary contains all expected metrics and calculations.
        """
        analyzer = TimeSeriesAnalyzer(sample_system_events_df, sample_commits_df)

        summary = analyzer.get_work_patterns_summary()

        # Verify summary structure
        assert "data_period" in summary
        assert "work_sessions" in summary
        assert "commits" in summary
        assert "productivity_metrics" in summary

        # Verify data period information
        assert "system_events" in summary["data_period"]
        assert "commits" in summary["data_period"]

        # Verify work session metrics
        assert "total_sessions" in summary["work_sessions"]
        assert "avg_duration_minutes" in summary["work_sessions"]
        assert "total_work_hours" in summary["work_sessions"]

        # Verify commit metrics
        assert "total_commits" in summary["commits"]
        assert "wbso_commits" in summary["commits"]
        assert "wbso_percentage" in summary["commits"]

    def test_get_work_patterns_summary_empty_data(self):
        """As a user I want to handle empty data gracefully, so I can work with incomplete datasets.
        Technical: Tests work pattern summary generation with empty data.
        Validation: Verifies summary is generated without errors even with empty DataFrames.
        """
        analyzer = TimeSeriesAnalyzer(pd.DataFrame(), pd.DataFrame())

        summary = analyzer.get_work_patterns_summary()

        # Verify summary structure is still present
        assert "data_period" in summary
        assert "work_sessions" in summary
        assert "commits" in summary
        assert "productivity_metrics" in summary


class TestIntegrationWithUnifiedDateTime:
    """Test integration with UnifiedDateTime system from TASK-029."""

    def test_datetime_parsing_integration(self):
        """As a user I want consistent datetime handling, so I can work with data from various sources.
        Technical: Tests integration with UnifiedDateTime system for consistent datetime parsing.
        Validation: Verifies various datetime formats are correctly parsed and converted.
        """
        # Test various datetime formats that UnifiedDateTime should handle
        test_formats = [
            "2025-01-15 08:00:00",  # Standard format
            "2025-01-15T08:00:00",  # ISO format
            "1/15/2025 8:00:00 AM",  # US format with AM/PM
            "2025/01/15 08:00:00",  # Alternative format
        ]

        for dt_str in test_formats:
            # Test that UnifiedDateTime can parse the format
            unified_dt = UnifiedDateTime(dt_str)
            assert unified_dt.is_valid(), f"Failed to parse: {dt_str}"

            # Test that the parsed datetime is reasonable
            parsed_dt = unified_dt.to_datetime()
            assert parsed_dt.year == 2025
            assert parsed_dt.month == 1
            assert parsed_dt.day == 15
            assert parsed_dt.hour == 8

    def test_data_loader_datetime_integration(self):
        """As a user I want consistent datetime handling in data loading, so I can work with various data sources.
        Technical: Tests that data loading utilities use UnifiedDateTime for consistent parsing.
        Validation: Verifies data loading handles various datetime formats correctly.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = temp_path / "test_events.csv"

            # Create test data with different datetime formats
            test_data = [
                {
                    "TimeGenerated": "2025-01-15 08:00:00",  # Standard format
                    "EventType": "startup",
                    "EventID": 6005,
                    "ComputerName": "WORKSTATION-01",
                },
                {
                    "TimeGenerated": "1/15/2025 5:30:00 PM",  # US format with PM
                    "EventType": "shutdown",
                    "EventID": 1074,
                    "ComputerName": "WORKSTATION-01",
                },
            ]

            pd.DataFrame(test_data).to_csv(csv_file, index=False)

            # Load data and verify datetime parsing
            result_df = load_system_events_data(temp_path)

            assert len(result_df) == 2
            assert isinstance(result_df["timestamp"].iloc[0], pd.Timestamp)
            assert isinstance(result_df["timestamp"].iloc[1], pd.Timestamp)

            # Verify times are correctly parsed
            assert result_df["timestamp"].iloc[0].hour == 8  # 8:00 AM
            assert result_df["timestamp"].iloc[1].hour == 17  # 5:30 PM
