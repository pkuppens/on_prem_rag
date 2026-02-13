"""Time series analysis framework for work session data.

This module provides pandas-based time series analysis capabilities for work session tracking,
commit correlation, and time-based insights generation.

See project/team/tasks/TASK-030.md for detailed requirements and implementation decisions.
"""

import logging
from typing import Dict, List, Tuple

import pandas as pd

from ..datetime_utils import UnifiedDateTime

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """Pandas-based time series analysis for work session data.

    This class provides comprehensive time series analysis capabilities for analyzing
    work patterns, commit frequencies, and time-based insights using pandas operations.
    """

    def __init__(self, system_events_df: pd.DataFrame, commits_df: pd.DataFrame):
        """Initialize with system events and commits data.

        As a user I want to initialize the analyzer with my data, so I can
        perform time series analysis on work sessions and commits.

        Technical: Validates input DataFrames and prepares them for analysis
        with proper datetime indexing and data validation.

        Args:
            system_events_df: DataFrame with system events data (should have datetime index)
            commits_df: DataFrame with commit data (should have datetime index)

        Raises:
            ValueError: If DataFrames don't have proper datetime index or required columns
        """
        self.system_events_df = system_events_df.copy()
        self.commits_df = commits_df.copy()

        # Validate DataFrames
        self._validate_dataframes()

        # Prepare data for analysis
        self._prepare_data()

        logger.info(
            f"TimeSeriesAnalyzer initialized with {len(self.system_events_df)} system events and {len(self.commits_df)} commits"
        )

    def _validate_dataframes(self) -> None:
        """Validate input DataFrames have required structure.

        Raises:
            ValueError: If DataFrames don't meet requirements
        """
        # Check system events DataFrame
        if not self.system_events_df.empty:
            if not isinstance(self.system_events_df.index, pd.DatetimeIndex):
                raise ValueError("System events DataFrame must have datetime index")

            required_columns = ["event_type", "event_id", "computer_name"]
            missing_columns = [col for col in required_columns if col not in self.system_events_df.columns]
            if missing_columns:
                raise ValueError(f"System events DataFrame missing columns: {missing_columns}")

        # Check commits DataFrame
        if not self.commits_df.empty:
            if not isinstance(self.commits_df.index, pd.DatetimeIndex):
                raise ValueError("Commits DataFrame must have datetime index")

            required_columns = ["repo_name", "author", "message", "is_wbso"]
            missing_columns = [col for col in required_columns if col not in self.commits_df.columns]
            if missing_columns:
                raise ValueError(f"Commits DataFrame missing columns: {missing_columns}")

    def _prepare_data(self) -> None:
        """Prepare data for analysis with additional computed columns."""
        # Add computed columns for system events
        if not self.system_events_df.empty:
            # Add session indicators
            self.system_events_df["is_startup"] = self.system_events_df["event_type"].str.contains(
                "startup|logon|login", case=False, na=False
            )
            self.system_events_df["is_shutdown"] = self.system_events_df["event_type"].str.contains(
                "shutdown|logoff|logout", case=False, na=False
            )

            # Add time-based columns
            self.system_events_df["hour"] = self.system_events_df.index.hour
            self.system_events_df["day_of_week"] = self.system_events_df.index.dayofweek
            self.system_events_df["date"] = self.system_events_df.index.date

        # Add computed columns for commits
        if not self.commits_df.empty:
            # Add time-based columns
            self.commits_df["hour"] = self.commits_df.index.hour
            self.commits_df["day_of_week"] = self.commits_df.index.dayofweek
            self.commits_df["date"] = self.commits_df.index.date

            # Add message length
            self.commits_df["message_length"] = self.commits_df["message"].str.len()

    def filter_by_time_range(self, start_time: str, end_time: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Filter data by time range for zoom operations.

        As a user I want to filter data by time range, so I can
        focus on specific periods for detailed analysis.

        Technical: Efficiently filters DataFrames using pandas datetime indexing
        with support for various time string formats.

        Args:
            start_time: Start time string (various formats supported)
            end_time: End time string (various formats supported)

        Returns:
            Tuple of (filtered_system_events_df, filtered_commits_df)

        Raises:
            ValueError: If time strings cannot be parsed
        """
        try:
            # Parse time strings using UnifiedDateTime
            start_dt = UnifiedDateTime(start_time)
            end_dt = UnifiedDateTime(end_time)

            if not start_dt.is_valid() or not end_dt.is_valid():
                raise ValueError("Invalid time format provided")

            start_timestamp = pd.Timestamp(start_dt.to_datetime())
            end_timestamp = pd.Timestamp(end_dt.to_datetime())

            # Filter system events
            filtered_system_events = pd.DataFrame()
            if not self.system_events_df.empty:
                mask = (self.system_events_df.index >= start_timestamp) & (self.system_events_df.index <= end_timestamp)
                filtered_system_events = self.system_events_df[mask].copy()

            # Filter commits
            filtered_commits = pd.DataFrame()
            if not self.commits_df.empty:
                mask = (self.commits_df.index >= start_timestamp) & (self.commits_df.index <= end_timestamp)
                filtered_commits = self.commits_df[mask].copy()

            logger.info(f"Filtered to {len(filtered_system_events)} system events and {len(filtered_commits)} commits")
            return filtered_system_events, filtered_commits

        except Exception as e:
            raise ValueError(f"Error filtering by time range: {e}")

    def aggregate_by_period(self, period: str) -> pd.DataFrame:
        """Aggregate data by hour/day/week/month.

        As a user I want to aggregate data by time periods, so I can
        analyze patterns and trends over different time scales.

        Technical: Uses pandas resampling to aggregate data by specified periods
        with comprehensive statistics for both system events and commits.

        Args:
            period: Aggregation period ('H'=hour, 'D'=day, 'W'=week, 'M'=month)

        Returns:
            DataFrame with aggregated statistics

        Raises:
            ValueError: If period is not supported
        """
        valid_periods = ["H", "D", "W", "M"]
        if period not in valid_periods:
            raise ValueError(f"Period must be one of {valid_periods}")

        aggregated_data = []

        # Aggregate system events
        if not self.system_events_df.empty:
            system_agg = (
                self.system_events_df.resample(period)
                .agg({"event_id": "count", "is_startup": "sum", "is_shutdown": "sum", "computer_name": "nunique"})
                .rename(
                    columns={
                        "event_id": "system_events_count",
                        "is_startup": "startup_events",
                        "is_shutdown": "shutdown_events",
                        "computer_name": "unique_computers",
                    }
                )
            )
            aggregated_data.append(system_agg)

        # Aggregate commits
        if not self.commits_df.empty:
            commits_agg = self.commits_df.resample(period).agg(
                {
                    "message": "count",
                    "is_wbso": "sum",
                    "author": "nunique",
                    "repo_name": "nunique",
                    "message_length": ["mean", "std"],
                }
            )

            # Flatten column names
            commits_agg.columns = [
                "commits_count",
                "wbso_commits",
                "unique_authors",
                "unique_repos",
                "avg_message_length",
                "std_message_length",
            ]
            aggregated_data.append(commits_agg)

        # Combine aggregations
        if aggregated_data:
            result = pd.concat(aggregated_data, axis=1)
            result = result.fillna(0)  # Fill NaN with 0 for missing periods
        else:
            result = pd.DataFrame()

        logger.info(f"Aggregated data by {period} period: {len(result)} periods")
        return result

    def detect_work_sessions(self) -> pd.DataFrame:
        """Detect work sessions using pandas operations.

        As a user I want to detect work sessions from system events, so I can
        understand my work patterns and correlate them with commits.

        Technical: Analyzes system events to identify work sessions based on
        startup/shutdown patterns and activity gaps.

        Returns:
            DataFrame with detected work sessions including start/end times and duration
        """
        if self.system_events_df.empty:
            logger.warning("No system events data available for session detection")
            return pd.DataFrame(columns=["session_start", "session_end", "duration_minutes", "computer_name"])

        sessions = []

        # Group by computer name to detect sessions per computer
        for computer_name, computer_events in self.system_events_df.groupby("computer_name"):
            computer_sessions = self._detect_sessions_for_computer(computer_events, computer_name)
            sessions.extend(computer_sessions)

        if not sessions:
            logger.warning("No work sessions detected")
            return pd.DataFrame(columns=["session_start", "session_end", "duration_minutes", "computer_name"])

        # Convert to DataFrame
        sessions_df = pd.DataFrame(sessions)
        sessions_df["duration_minutes"] = (sessions_df["session_end"] - sessions_df["session_start"]).dt.total_seconds() / 60

        # Sort by session start time
        sessions_df = sessions_df.sort_values("session_start").reset_index(drop=True)

        logger.info(f"Detected {len(sessions_df)} work sessions")
        return sessions_df

    def _detect_sessions_for_computer(self, events: pd.DataFrame, computer_name: str) -> List[Dict]:
        """Detect work sessions for a specific computer.

        Args:
            events: System events for a specific computer
            computer_name: Name of the computer

        Returns:
            List of session dictionaries
        """
        sessions = []
        current_session_start = None

        # Sort events by timestamp
        events = events.sort_index()

        for timestamp, event in events.iterrows():
            if event["is_startup"] and current_session_start is None:
                # Start of new session
                current_session_start = timestamp
            elif event["is_shutdown"] and current_session_start is not None:
                # End of current session
                sessions.append({"session_start": current_session_start, "session_end": timestamp, "computer_name": computer_name})
                current_session_start = None

        # Handle session that's still active (no shutdown event)
        if current_session_start is not None:
            # Assume session ends at last event time
            last_event_time = events.index[-1]
            sessions.append(
                {"session_start": current_session_start, "session_end": last_event_time, "computer_name": computer_name}
            )

        return sessions

    def correlate_commits_with_sessions(self) -> pd.DataFrame:
        """Correlate commits with work sessions.

        As a user I want to correlate commits with work sessions, so I can
        understand which commits were made during active work periods.

        Technical: Matches commits to work sessions using time-based overlap
        analysis with pandas operations for efficient correlation.

        Returns:
            DataFrame with commits and their associated work sessions
        """
        if self.commits_df.empty:
            logger.warning("No commits data available for correlation")
            return pd.DataFrame()

        # Detect work sessions
        sessions_df = self.detect_work_sessions()
        if sessions_df.empty:
            logger.warning("No work sessions available for correlation")
            return self.commits_df.assign(session_id=None, session_duration_minutes=None)

        # Create correlation results
        correlated_commits = []

        for commit_time, commit in self.commits_df.iterrows():
            # Find sessions that overlap with commit time
            overlapping_sessions = sessions_df[
                (sessions_df["session_start"] <= commit_time) & (sessions_df["session_end"] >= commit_time)
            ]

            if not overlapping_sessions.empty:
                # Use the longest overlapping session
                longest_session = overlapping_sessions.loc[overlapping_sessions["duration_minutes"].idxmax()]
                correlated_commits.append(
                    {
                        **commit.to_dict(),
                        "session_id": f"{longest_session['computer_name']}_{longest_session['session_start'].strftime('%Y%m%d_%H%M%S')}",
                        "session_duration_minutes": longest_session["duration_minutes"],
                        "session_start": longest_session["session_start"],
                        "session_end": longest_session["session_end"],
                    }
                )
            else:
                # Commit outside any work session
                correlated_commits.append(
                    {
                        **commit.to_dict(),
                        "session_id": None,
                        "session_duration_minutes": None,
                        "session_start": None,
                        "session_end": None,
                    }
                )

        result_df = pd.DataFrame(correlated_commits)
        result_df.index = self.commits_df.index  # Preserve original index

        # Calculate statistics
        total_commits = len(result_df)
        commits_in_sessions = len(result_df[result_df["session_id"].notna()])
        correlation_rate = commits_in_sessions / total_commits if total_commits > 0 else 0

        logger.info(f"Correlated {commits_in_sessions}/{total_commits} commits with work sessions ({correlation_rate:.1%})")
        return result_df

    def get_work_patterns_summary(self) -> Dict:
        """Get summary of work patterns and statistics.

        As a user I want to get a summary of my work patterns, so I can
        understand my productivity and work habits.

        Technical: Generates comprehensive statistics about work patterns,
        commit frequencies, and time-based insights.

        Returns:
            Dictionary with work pattern statistics
        """
        summary = {"data_period": {}, "work_sessions": {}, "commits": {}, "productivity_metrics": {}}

        # Data period information
        if not self.system_events_df.empty:
            summary["data_period"]["system_events"] = {
                "start": self.system_events_df.index.min().isoformat(),
                "end": self.system_events_df.index.max().isoformat(),
                "total_events": len(self.system_events_df),
            }

        if not self.commits_df.empty:
            summary["data_period"]["commits"] = {
                "start": self.commits_df.index.min().isoformat(),
                "end": self.commits_df.index.max().isoformat(),
                "total_commits": len(self.commits_df),
            }

        # Work session analysis
        sessions_df = self.detect_work_sessions()
        if not sessions_df.empty:
            summary["work_sessions"] = {
                "total_sessions": len(sessions_df),
                "avg_duration_minutes": sessions_df["duration_minutes"].mean(),
                "total_work_hours": sessions_df["duration_minutes"].sum() / 60,
                "sessions_per_day": len(sessions_df)
                / max(1, (sessions_df["session_end"].max() - sessions_df["session_start"].min()).days),
            }

        # Commit analysis
        if not self.commits_df.empty:
            wbso_commits = self.commits_df[self.commits_df["is_wbso"]]
            summary["commits"] = {
                "total_commits": len(self.commits_df),
                "wbso_commits": len(wbso_commits),
                "wbso_percentage": len(wbso_commits) / len(self.commits_df) * 100,
                "commits_per_day": len(self.commits_df) / max(1, (self.commits_df.index.max() - self.commits_df.index.min()).days),
                "unique_authors": self.commits_df["author"].nunique(),
                "unique_repos": self.commits_df["repo_name"].nunique(),
            }

        # Productivity metrics
        if not sessions_df.empty and not self.commits_df.empty:
            correlated_commits = self.correlate_commits_with_sessions()
            commits_in_sessions = correlated_commits[correlated_commits["session_id"].notna()]

            if not commits_in_sessions.empty:
                summary["productivity_metrics"] = {
                    "commits_per_work_hour": len(commits_in_sessions) / max(1, sessions_df["duration_minutes"].sum() / 60),
                    "session_commit_correlation": len(commits_in_sessions) / len(self.commits_df) * 100,
                    "avg_commits_per_session": len(commits_in_sessions) / len(sessions_df),
                }

        return summary
