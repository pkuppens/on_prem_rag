"""Data loading utilities for system events and commit data.

This module provides functions to load and prepare data from various sources
into pandas DataFrames for time series analysis.

See project/team/tasks/TASK-030.md for detailed requirements and implementation decisions.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from ..datetime_utils import UnifiedDateTime

logger = logging.getLogger(__name__)


def load_system_events_data(data_dir: Path) -> pd.DataFrame:
    """Load and combine all system events CSV files into a single DataFrame.

    As a user I want to load all system events data into a unified format, so I can
    analyze work patterns and session detection across multiple data sources.

    Technical: Combines multiple CSV files with system events into a single DataFrame
    with standardized datetime formatting and proper data types.

    Args:
        data_dir: Directory containing system events CSV files

    Returns:
        DataFrame with system events data including timestamp, event_type, event_id, computer_name

    Raises:
        FileNotFoundError: If data directory doesn't exist
        ValueError: If no valid CSV files found
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in directory: {data_dir}")

    logger.info(f"Loading system events from {len(csv_files)} CSV files")

    all_data = []

    for csv_file in csv_files:
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)

            # Standardize column names (handle different naming conventions)
            column_mapping = {
                "TimeGenerated": "timestamp",
                "Time Generated": "timestamp",
                "Time": "timestamp",
                "EventType": "event_type",
                "Event Type": "event_type",
                "EventID": "event_id",
                "Event ID": "event_id",
                "ComputerName": "computer_name",
                "Computer Name": "computer_name",
                "Computer": "computer_name",
            }

            df = df.rename(columns=column_mapping)

            # Ensure required columns exist
            required_columns = ["timestamp", "event_type", "event_id", "computer_name"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                logger.warning(f"Missing columns in {csv_file}: {missing_columns}")
                continue

            # Convert timestamp to standardized format
            df["timestamp"] = df["timestamp"].apply(_convert_timestamp_to_datetime)

            # Filter out invalid timestamps
            df = df[df["timestamp"].notna()]

            if len(df) > 0:
                all_data.append(df)
                logger.info(f"Loaded {len(df)} events from {csv_file.name}")
            else:
                logger.warning(f"No valid events found in {csv_file.name}")

        except Exception as e:
            logger.error(f"Error loading {csv_file}: {e}")
            continue

    if not all_data:
        raise ValueError("No valid data loaded from any CSV files")

    # Combine all DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)

    # Sort by timestamp
    combined_df = combined_df.sort_values("timestamp").reset_index(drop=True)

    # Optimize data types
    combined_df = _optimize_dataframe_types(combined_df)

    logger.info(f"Successfully loaded {len(combined_df)} system events")
    return combined_df


def load_commits_data(commits_file: Path) -> pd.DataFrame:
    """Load processed commits JSON into a pandas DataFrame.

    As a user I want to load commit data into a structured format, so I can
    correlate commits with work sessions and analyze development patterns.

    Technical: Loads JSON data with commit information and converts to DataFrame
    with proper datetime formatting and data type optimization.

    Args:
        commits_file: Path to JSON file containing commit data

    Returns:
        DataFrame with commit data including timestamp, repo_name, author, message, is_wbso

    Raises:
        FileNotFoundError: If commits file doesn't exist
        ValueError: If JSON data is invalid or missing required fields
    """
    if not commits_file.exists():
        raise FileNotFoundError(f"Commits file not found: {commits_file}")

    try:
        with open(commits_file, "r", encoding="utf-8") as f:
            commits_data = json.load(f)

        if not isinstance(commits_data, list):
            raise ValueError("Commits data must be a list of commit objects")

        if not commits_data:
            logger.warning("No commits found in file")
            return pd.DataFrame(columns=["timestamp", "repo_name", "author", "message", "is_wbso"])

        # Convert to DataFrame
        df = pd.DataFrame(commits_data)

        # Standardize column names
        column_mapping = {
            "commit_time": "timestamp",
            "commit_timestamp": "timestamp",
            "time": "timestamp",
            "repository": "repo_name",
            "repo": "repo_name",
            "commit_message": "message",
            "msg": "message",
            "wbso_eligible": "is_wbso",
            "wbso": "is_wbso",
        }

        df = df.rename(columns=column_mapping)

        # Ensure required columns exist
        required_columns = ["timestamp", "repo_name", "author", "message", "is_wbso"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Convert timestamp to standardized format
        df["timestamp"] = df["timestamp"].apply(_convert_timestamp_to_datetime)

        # Filter out invalid timestamps
        df = df[df["timestamp"].notna()]

        # Ensure is_wbso is boolean
        df["is_wbso"] = df["is_wbso"].astype(bool)

        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Optimize data types
        df = _optimize_dataframe_types(df)

        logger.info(f"Successfully loaded {len(df)} commits")
        return df

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in commits file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading commits data: {e}")


def prepare_time_series_data(system_events_df: pd.DataFrame, commits_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare data for time series analysis with proper datetime indexing.

    As a user I want to prepare data for time series analysis, so I can
    perform efficient time-based operations and aggregations.

    Technical: Sets datetime index and ensures data is properly formatted
    for pandas time series operations with performance optimizations.

    Args:
        system_events_df: DataFrame with system events data
        commits_df: DataFrame with commit data

    Returns:
        Tuple of (prepared_system_events_df, prepared_commits_df) with datetime index

    Raises:
        ValueError: If DataFrames don't have valid timestamp columns
    """
    if system_events_df.empty and commits_df.empty:
        logger.warning("Both DataFrames are empty")
        return system_events_df, commits_df

    prepared_system_events = system_events_df.copy()
    prepared_commits = commits_df.copy()

    # Prepare system events DataFrame
    if not prepared_system_events.empty:
        if "timestamp" not in prepared_system_events.columns:
            raise ValueError("System events DataFrame missing 'timestamp' column")

        # Set datetime index
        prepared_system_events = prepared_system_events.set_index("timestamp")

        # Sort by index
        prepared_system_events = prepared_system_events.sort_index()

        # Remove duplicate timestamps (keep first occurrence)
        prepared_system_events = prepared_system_events[~prepared_system_events.index.duplicated(keep="first")]

        logger.info(f"Prepared {len(prepared_system_events)} system events for time series analysis")

    # Prepare commits DataFrame
    if not prepared_commits.empty:
        if "timestamp" not in prepared_commits.columns:
            raise ValueError("Commits DataFrame missing 'timestamp' column")

        # Set datetime index
        prepared_commits = prepared_commits.set_index("timestamp")

        # Sort by index
        prepared_commits = prepared_commits.sort_index()

        # Remove duplicate timestamps (keep first occurrence)
        prepared_commits = prepared_commits[~prepared_commits.index.duplicated(keep="first")]

        logger.info(f"Prepared {len(prepared_commits)} commits for time series analysis")

    return prepared_system_events, prepared_commits


def _convert_timestamp_to_datetime(timestamp_str: str) -> Optional[pd.Timestamp]:
    """Convert timestamp string to pandas Timestamp using UnifiedDateTime.

    Args:
        timestamp_str: Timestamp string in various formats

    Returns:
        pandas Timestamp or None if conversion fails
    """
    if pd.isna(timestamp_str) or timestamp_str == "":
        return None

    try:
        # Use UnifiedDateTime for consistent parsing
        unified_dt = UnifiedDateTime(str(timestamp_str))

        if unified_dt.is_valid():
            return pd.Timestamp(unified_dt.to_datetime())
        else:
            logger.warning(f"Invalid timestamp: {timestamp_str}")
            return None

    except Exception as e:
        logger.warning(f"Error converting timestamp '{timestamp_str}': {e}")
        return None


def _optimize_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame data types for memory efficiency.

    Args:
        df: DataFrame to optimize

    Returns:
        Optimized DataFrame with efficient data types
    """
    optimized_df = df.copy()

    # Optimize string columns
    for col in optimized_df.select_dtypes(include=["object"]).columns:
        if optimized_df[col].dtype == "object":
            # Try to convert to category if it has many repeated values
            if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                optimized_df[col] = optimized_df[col].astype("category")

    # Optimize integer columns
    for col in optimized_df.select_dtypes(include=["int64"]).columns:
        if optimized_df[col].min() >= 0:
            if optimized_df[col].max() < 255:
                optimized_df[col] = optimized_df[col].astype("uint8")
            elif optimized_df[col].max() < 65535:
                optimized_df[col] = optimized_df[col].astype("uint16")
            elif optimized_df[col].max() < 4294967295:
                optimized_df[col] = optimized_df[col].astype("uint32")
        else:
            if optimized_df[col].min() > -128 and optimized_df[col].max() < 127:
                optimized_df[col] = optimized_df[col].astype("int8")
            elif optimized_df[col].min() > -32768 and optimized_df[col].max() < 32767:
                optimized_df[col] = optimized_df[col].astype("int16")
            elif optimized_df[col].min() > -2147483648 and optimized_df[col].max() < 2147483647:
                optimized_df[col] = optimized_df[col].astype("int32")

    return optimized_df
