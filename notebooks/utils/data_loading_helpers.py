"""Data loading utilities for time-based visualization analysis.

This module provides utilities for loading and preprocessing system events
and commit data for visualization in Jupyter notebooks.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


def safe_to_datetime_amsterdam(data: Union[pd.Series, str, List[str]], column_name: str = "timestamp") -> pd.Series:
    """Safely convert data to timezone-aware Amsterdam datetime.

    This function handles both timezone-naive and timezone-aware input data,
    ensuring consistent Amsterdam timezone output without raising errors.

    Args:
        data: Input data to convert (Series, string, or list of strings)
        column_name: Name of the column for error messages

    Returns:
        pandas Series with timezone-aware Amsterdam datetime

    Raises:
        ValueError: If data cannot be converted to datetime
    """
    # Convert to pandas Series if not already
    if not isinstance(data, pd.Series):
        data = pd.Series(data)

    # Convert to datetime first
    dt_series = pd.to_datetime(data, errors="coerce")

    # Check if any values are already timezone-aware
    has_timezone = dt_series.dt.tz is not None

    if has_timezone:
        # If already timezone-aware, convert to Amsterdam timezone
        return dt_series.dt.tz_convert("Europe/Amsterdam")
    else:
        # If timezone-naive, assume Amsterdam timezone and localize
        return dt_series.dt.tz_localize("Europe/Amsterdam")


def load_system_events_data(file_path: str) -> Dict[str, Any]:
    """Load processed system events data from JSON file.

    Args:
        file_path: Path to the all_system_events_processed.json file

    Returns:
        Dictionary containing system events data with work sessions

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"System events file not found: {file_path}")

    with open(path_obj, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def load_commits_data(file_path: str) -> Dict[str, Any]:
    """Load processed commits data from JSON file.

    Args:
        file_path: Path to the commits_processed.json file

    Returns:
        Dictionary containing commits data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Commits file not found: {file_path}")

    with open(path_obj, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def convert_work_sessions_to_dataframe(system_events_data: Dict[str, Any]) -> pd.DataFrame:
    """Convert work sessions from system events data to pandas DataFrame.

    Args:
        system_events_data: System events data dictionary

    Returns:
        DataFrame with work session information including start_time, end_time,
        duration_hours, and date columns
    """
    sessions = system_events_data.get("logon_logoff_sessions", [])

    if not sessions:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(sessions)

    # Convert timestamp columns to datetime with Amsterdam timezone
    df["start_time"] = safe_to_datetime_amsterdam(df["start_time"].tolist(), "start_time")
    df["end_time"] = safe_to_datetime_amsterdam(df["end_time"].tolist(), "end_time")
    df["date"] = pd.to_datetime(df["date"])

    # Sort by start time
    df = df.sort_values("start_time").reset_index(drop=True)

    return df


def convert_commits_to_dataframe(commits_data: Dict[str, Any]) -> pd.DataFrame:
    """Convert commits data to pandas DataFrame.

    Args:
        commits_data: Commits data dictionary

    Returns:
        DataFrame with commit information including timestamp, repo_name,
        author, message, and hash columns
    """
    commits = commits_data.get("commits", [])

    if not commits:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(commits)

    # Convert timestamp to datetime with Amsterdam timezone handling
    df["timestamp"] = safe_to_datetime_amsterdam(df["timestamp"].tolist(), "timestamp")

    # Sort by timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def filter_data_by_date_range(df: pd.DataFrame, start_date: str, end_date: str, date_column: str = "timestamp") -> pd.DataFrame:
    """Filter DataFrame by date range.

    Args:
        df: DataFrame to filter
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        date_column: Name of the date column to filter on

    Returns:
        Filtered DataFrame
    """
    start_dt = safe_to_datetime_amsterdam(start_date, "start_date").iloc[0]
    end_dt = safe_to_datetime_amsterdam(end_date, "end_date").iloc[0]

    # Filter data within date range
    mask = (df[date_column] >= start_dt) & (df[date_column] <= end_dt)
    filtered_df = df[mask].copy()  # type: ignore
    return filtered_df  # type: ignore


def get_active_repositories_in_range(commits_df: pd.DataFrame, start_date: str, end_date: str) -> List[str]:
    """Get list of repositories that have commits in the specified date range.

    Args:
        commits_df: DataFrame with commits data
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        List of repository names that have commits in the date range
    """
    filtered_commits = filter_data_by_date_range(commits_df, start_date, end_date, "timestamp")

    if filtered_commits.empty:
        return []

    return sorted(filtered_commits["repo_name"].unique().tolist())


def prepare_work_sessions_for_timeline(work_sessions_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare work sessions data for timeline visualization.

    Args:
        work_sessions_df: DataFrame with work session data

    Returns:
        DataFrame prepared for timeline plotting with proper datetime indexing
    """
    if work_sessions_df.empty:
        return pd.DataFrame()

    # Create a copy to avoid modifying original
    df = work_sessions_df.copy()

    # Ensure we have the required columns
    required_cols = ["start_time", "end_time", "duration_hours", "date"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Add session duration in minutes for better visualization
    df["duration_minutes"] = df["duration_hours"] * 60

    # Add session type for styling
    df["session_type"] = df.get("session_type", "unknown")

    return df


def prepare_commits_for_overlay(commits_df: pd.DataFrame, active_repos: Optional[List[str]] = None) -> pd.DataFrame:
    """Prepare commits data for overlay visualization.

    Args:
        commits_df: DataFrame with commits data
        active_repos: Optional list of active repositories to filter by

    Returns:
        DataFrame prepared for overlay plotting
    """
    if commits_df.empty:
        return pd.DataFrame()

    # Create a copy to avoid modifying original
    df = commits_df.copy()

    # Filter by active repositories if specified
    if active_repos:
        df = df[df["repo_name"].isin(active_repos)].copy()

    # Ensure we have the required columns
    required_cols = ["timestamp", "repo_name", "author", "message"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Add commit date for grouping
    timestamp_series = df["timestamp"]
    df["commit_date"] = timestamp_series.dt.date  # type: ignore

    return df  # type: ignore
