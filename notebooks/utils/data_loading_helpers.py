"""Data loading utilities for time-based visualization analysis.

This module provides utilities for loading and preprocessing system events
and commit data for visualization in Jupyter notebooks.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


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
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"System events file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
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
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Commits file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
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

    # Convert timestamp columns to datetime with UTC timezone
    df["start_time"] = pd.to_datetime(df["start_time"]).dt.tz_localize("UTC")
    df["end_time"] = pd.to_datetime(df["end_time"]).dt.tz_localize("UTC")
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

    # Convert timestamp to datetime with UTC timezone handling
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

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
    start_dt = pd.to_datetime(start_date).tz_localize("UTC")
    end_dt = pd.to_datetime(end_date).tz_localize("UTC")

    # Filter data within date range
    mask = (df[date_column] >= start_dt) & (df[date_column] <= end_dt)
    return df[mask].copy()


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
    df["commit_date"] = df["timestamp"].dt.date

    return df
