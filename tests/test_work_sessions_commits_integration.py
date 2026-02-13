#!/usr/bin/env python3
"""Unit tests for work sessions and commits integration functionality.

This module tests the integration of work sessions from system events with git commits
to create comprehensive work logs for WBSO compliance.

See docs/technical/WBSO_COMPLIANCE.md for business context and requirements.
"""

# Import the functions to test
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / "docs" / "project" / "hours" / "scripts"))

from integrate_work_sessions_commits import (
    assign_commits_to_sessions,
    calculate_summary_statistics,
    filter_commits_by_date,
    group_unassigned_commits_by_date,
    parse_commit_timestamp,
    parse_work_session_timestamp,
)


class TestTimestampParsing:
    """Test timestamp parsing functionality for both commit and work session formats."""

    def test_parse_commit_timestamp_with_timezone(self):
        """As a user I want commit timestamps with timezone info to be parsed correctly, so I can accurately match commits to work sessions.
        Technical: Parse ISO 8601 timestamp with timezone offset.
        Validation: Verify datetime object is created with correct timezone info.
        """
        timestamp_str = "2025-05-15T14:30:45+02:00"
        result = parse_commit_timestamp(timestamp_str)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo is not None

    def test_parse_commit_timestamp_utc(self):
        """As a user I want UTC commit timestamps to be parsed correctly, so I can handle commits from different timezones.
        Technical: Parse ISO 8601 timestamp with UTC timezone.
        Validation: Verify UTC timezone is preserved in parsed datetime.
        """
        timestamp_str = "2025-05-15T12:30:45+00:00"
        result = parse_commit_timestamp(timestamp_str)

        assert isinstance(result, datetime)
        assert result.tzinfo.utcoffset(None).total_seconds() == 0  # UTC offset is 0

    def test_parse_commit_timestamp_invalid_format(self):
        """As a user I want invalid commit timestamps to raise clear errors, so I can identify data quality issues.
        Technical: Handle malformed timestamp strings gracefully.
        Validation: Verify ValueError is raised with descriptive message.
        """
        with pytest.raises(ValueError, match="Failed to parse commit timestamp"):
            parse_commit_timestamp("invalid-timestamp")

    def test_parse_work_session_timestamp_local_format(self):
        """As a user I want work session timestamps in local format to be parsed correctly, so I can match them with commits.
        Technical: Parse local timestamp format and convert to timezone-aware datetime.
        Validation: Verify datetime object is created with UTC timezone for consistency.
        """
        timestamp_str = "2025-05-15 14:30:45"
        result = parse_work_session_timestamp(timestamp_str)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 5
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo is not None  # Should be timezone-aware

    def test_parse_work_session_timestamp_invalid_format(self):
        """As a user I want invalid work session timestamps to raise clear errors, so I can identify data quality issues.
        Technical: Handle malformed timestamp strings gracefully.
        Validation: Verify ValueError is raised with descriptive message.
        """
        with pytest.raises(ValueError, match="Failed to parse work session timestamp"):
            parse_work_session_timestamp("invalid-timestamp")


class TestCommitFiltering:
    """Test commit filtering by date functionality."""

    def test_filter_commits_by_date_includes_recent_commits(self):
        """As a user I want only commits from the specified start date onwards to be processed, so I can focus on recent work activity.
        Technical: Filter commits based on timestamp >= start_date.
        Validation: Verify only commits from start_date onwards are included.
        """
        commits = [
            {"timestamp": "2025-04-30T10:00:00+00:00", "hash": "commit1", "message": "Old commit"},
            {"timestamp": "2025-05-01T10:00:00+00:00", "hash": "commit2", "message": "Start date commit"},
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "commit3", "message": "Recent commit"},
        ]

        filtered = filter_commits_by_date(commits, "2025-05-01")

        assert len(filtered) == 2
        assert filtered[0]["hash"] == "commit2"
        assert filtered[1]["hash"] == "commit3"

    def test_filter_commits_by_date_excludes_old_commits(self):
        """As a user I want commits before the start date to be excluded, so I can focus on relevant work periods.
        Technical: Exclude commits with timestamp < start_date.
        Validation: Verify commits before start_date are not included.
        """
        commits = [
            {"timestamp": "2025-04-30T23:59:59+00:00", "hash": "old_commit", "message": "Just before start date"},
            {"timestamp": "2025-05-01T00:00:00+00:00", "hash": "start_commit", "message": "Exactly at start date"},
        ]

        filtered = filter_commits_by_date(commits, "2025-05-01")

        assert len(filtered) == 1
        assert filtered[0]["hash"] == "start_commit"

    def test_filter_commits_by_date_handles_invalid_timestamps(self):
        """As a user I want commits with invalid timestamps to be skipped gracefully, so I can process data with quality issues.
        Technical: Skip commits that cannot be parsed due to invalid timestamps.
        Validation: Verify invalid commits are excluded without causing errors.
        """
        commits = [
            {"timestamp": "invalid-timestamp", "hash": "bad_commit", "message": "Invalid timestamp"},
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "good_commit", "message": "Valid timestamp"},
        ]

        filtered = filter_commits_by_date(commits, "2025-05-01")

        assert len(filtered) == 1
        assert filtered[0]["hash"] == "good_commit"


class TestCommitAssignment:
    """Test commit assignment to work sessions functionality."""

    def test_assign_commits_to_sessions_within_time_range(self):
        """As a user I want commits that fall within work session time ranges to be assigned correctly, so I can track development activity.
        Technical: Assign commits where commit_timestamp >= session_start AND commit_timestamp <= session_end.
        Validation: Verify commits within time range are assigned to correct session.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "2025-05-15 09:00:00", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "commit1", "message": "Morning commit", "is_wbso": True},
            {"timestamp": "2025-05-15T15:00:00+00:00", "hash": "commit2", "message": "Afternoon commit", "is_wbso": False},
        ]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert len(enhanced_sessions) == 1
        assert len(enhanced_sessions[0]["assigned_commits"]) == 2
        assert enhanced_sessions[0]["commit_count"] == 2
        assert enhanced_sessions[0]["is_wbso"]  # Promoted due to WBSO commit
        assert len(unassigned) == 0

    def test_assign_commits_to_sessions_outside_time_range(self):
        """As a user I want commits outside work session time ranges to remain unassigned, so I can identify work done outside tracked sessions.
        Technical: Do not assign commits where timestamp is outside session time range.
        Validation: Verify commits outside time range are marked as unassigned.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "2025-05-15 09:00:00", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [
            {"timestamp": "2025-05-15T08:00:00+00:00", "hash": "early_commit", "message": "Before session", "is_wbso": True},
            {"timestamp": "2025-05-15T18:00:00+00:00", "hash": "late_commit", "message": "After session", "is_wbso": True},
        ]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert len(enhanced_sessions) == 1
        assert len(enhanced_sessions[0]["assigned_commits"]) == 0
        assert enhanced_sessions[0]["commit_count"] == 0
        assert not enhanced_sessions[0]["is_wbso"]
        assert len(unassigned) == 2

    def test_wbso_eligibility_promotion(self):
        """As a user I want work sessions to be promoted to WBSO-eligible when they contain WBSO commits, so I can track eligible work hours.
        Technical: Set is_wbso=True on work session if ANY assigned commit has is_wbso=True.
        Validation: Verify session is promoted when containing WBSO commits.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "2025-05-15 09:00:00", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "wbso_commit", "message": "WBSO eligible commit", "is_wbso": True},
            {"timestamp": "2025-05-15T15:00:00+00:00", "hash": "non_wbso_commit", "message": "Non-WBSO commit", "is_wbso": False},
        ]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert enhanced_sessions[0]["is_wbso"]  # Promoted due to WBSO commit

    def test_multiple_commits_per_session(self):
        """As a user I want multiple commits to be assignable to a single work session, so I can track all development activity during a session.
        Technical: Allow multiple commits per work session within time range.
        Validation: Verify all commits within time range are assigned to the session.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "2025-05-15 09:00:00", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "commit1", "message": "First commit", "is_wbso": True},
            {"timestamp": "2025-05-15T12:00:00+00:00", "hash": "commit2", "message": "Second commit", "is_wbso": False},
            {"timestamp": "2025-05-15T16:00:00+00:00", "hash": "commit3", "message": "Third commit", "is_wbso": True},
        ]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert len(enhanced_sessions[0]["assigned_commits"]) == 3
        assert enhanced_sessions[0]["commit_count"] == 3
        assert enhanced_sessions[0]["is_wbso"]  # Promoted due to WBSO commits


class TestUnassignedCommitsGrouping:
    """Test unassigned commits grouping by date functionality."""

    def test_group_unassigned_commits_by_date(self):
        """As a user I want unassigned commits to be grouped by date for easy review, so I can identify work done outside tracked sessions.
        Technical: Group commits by date string (YYYY-MM-DD) with count and commit list.
        Validation: Verify commits are properly grouped by date with correct counts.
        """
        unassigned_commits = [
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "commit1", "message": "Morning commit", "date": "2025-05-15"},
            {"timestamp": "2025-05-15T15:00:00+00:00", "hash": "commit2", "message": "Afternoon commit", "date": "2025-05-15"},
            {"timestamp": "2025-05-16T10:00:00+00:00", "hash": "commit3", "message": "Next day commit", "date": "2025-05-16"},
        ]

        grouped = group_unassigned_commits_by_date(unassigned_commits)

        assert "2025-05-15" in grouped
        assert "2025-05-16" in grouped
        assert grouped["2025-05-15"]["count"] == 2
        assert grouped["2025-05-16"]["count"] == 1
        assert len(grouped["2025-05-15"]["commits"]) == 2
        assert len(grouped["2025-05-16"]["commits"]) == 1

    def test_group_unassigned_commits_handles_invalid_timestamps(self):
        """As a user I want commits with invalid timestamps to be skipped during grouping, so I can process data with quality issues.
        Technical: Skip commits that cannot be parsed during grouping process.
        Validation: Verify invalid commits are excluded from grouping without errors.
        """
        unassigned_commits = [
            {"timestamp": "invalid-timestamp", "hash": "bad_commit", "message": "Invalid timestamp"},
            {"timestamp": "2025-05-15T10:00:00+00:00", "hash": "good_commit", "message": "Valid timestamp"},
        ]

        grouped = group_unassigned_commits_by_date(unassigned_commits)

        assert "2025-05-15" in grouped
        assert grouped["2025-05-15"]["count"] == 1
        assert len(grouped["2025-05-15"]["commits"]) == 1


class TestSummaryStatistics:
    """Test summary statistics calculation functionality."""

    def test_calculate_summary_statistics_comprehensive(self):
        """As a user I want comprehensive summary statistics to be calculated, so I can understand work activity and WBSO compliance.
        Technical: Calculate totals, rates, and percentages for work sessions and commits.
        Validation: Verify all summary metrics are calculated correctly.
        """
        enhanced_sessions = [
            {"session_id": "session_001", "work_hours": 8.0, "is_wbso": True, "commit_count": 2},
            {"session_id": "session_002", "work_hours": 6.0, "is_wbso": False, "commit_count": 1},
            {"session_id": "session_003", "work_hours": 4.0, "is_wbso": True, "commit_count": 0},
        ]

        commits = [
            {"hash": "commit1", "is_wbso": True},
            {"hash": "commit2", "is_wbso": True},
            {"hash": "commit3", "is_wbso": False},
        ]

        summary = calculate_summary_statistics(enhanced_sessions, commits, 2, 1)

        assert summary["total_work_sessions"] == 3
        assert summary["wbso_eligible_sessions"] == 2
        assert summary["total_work_hours"] == 18.0
        assert summary["wbso_work_hours"] == 12.0
        assert summary["total_commits_processed"] == 3
        assert summary["assigned_commits"] == 2
        assert summary["unassigned_commits"] == 1
        assert summary["assignment_rate"] == 66.7  # 2/3 * 100

    def test_calculate_summary_statistics_empty_data(self):
        """As a user I want summary statistics to handle empty data gracefully, so I can process periods with no work activity.
        Technical: Handle empty lists and zero values in calculations.
        Validation: Verify zero values are returned for empty data without errors.
        """
        enhanced_sessions = []
        commits = []

        summary = calculate_summary_statistics(enhanced_sessions, commits, 0, 0)

        assert summary["total_work_sessions"] == 0
        assert summary["wbso_eligible_sessions"] == 0
        assert summary["total_work_hours"] == 0.0
        assert summary["wbso_work_hours"] == 0.0
        assert summary["total_commits_processed"] == 0
        assert summary["assigned_commits"] == 0
        assert summary["unassigned_commits"] == 0
        assert summary["assignment_rate"] == 0.0


class TestIntegrationEdgeCases:
    """Test edge cases and boundary conditions for the integration process."""

    def test_commit_at_session_boundary_start(self):
        """As a user I want commits exactly at session start time to be assigned correctly, so I can capture all work activity.
        Technical: Handle commits with timestamp exactly equal to session start time.
        Validation: Verify boundary condition is handled correctly.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "2025-05-15 09:00:00", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [
            {
                "timestamp": "2025-05-15T09:00:00+00:00",  # Exactly at start
                "hash": "boundary_commit",
                "message": "Boundary commit",
                "is_wbso": True,
            }
        ]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert len(enhanced_sessions[0]["assigned_commits"]) == 1
        assert enhanced_sessions[0]["is_wbso"]

    def test_commit_at_session_boundary_end(self):
        """As a user I want commits exactly at session end time to be assigned correctly, so I can capture all work activity.
        Technical: Handle commits with timestamp exactly equal to session end time.
        Validation: Verify boundary condition is handled correctly.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "2025-05-15 09:00:00", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [
            {
                "timestamp": "2025-05-15T17:00:00+00:00",  # Exactly at end
                "hash": "boundary_commit",
                "message": "Boundary commit",
                "is_wbso": True,
            }
        ]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert len(enhanced_sessions[0]["assigned_commits"]) == 1
        assert enhanced_sessions[0]["is_wbso"]

    def test_session_with_invalid_timestamps(self):
        """As a user I want sessions with invalid timestamps to be handled gracefully, so I can process data with quality issues.
        Technical: Skip sessions that cannot be parsed due to invalid timestamps.
        Validation: Verify invalid sessions are preserved without commit assignments.
        """
        work_sessions = [
            {"session_id": "session_001", "start_time": "invalid-timestamp", "end_time": "2025-05-15 17:00:00", "work_hours": 8.0}
        ]

        commits = [{"timestamp": "2025-05-15T10:00:00+00:00", "hash": "commit1", "message": "Valid commit", "is_wbso": True}]

        enhanced_sessions, unassigned = assign_commits_to_sessions(work_sessions, commits)

        assert len(enhanced_sessions) == 1
        assert len(enhanced_sessions[0]["assigned_commits"]) == 0  # No commits assigned due to invalid timestamp
        assert len(unassigned) == 1  # Commit remains unassigned
