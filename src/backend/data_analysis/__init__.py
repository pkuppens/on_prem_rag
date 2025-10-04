"""Data analysis module for time-based analytics and insights.

This module provides pandas-based data analysis capabilities for work session tracking,
commit correlation, and time-based insights generation.

See project/team/tasks/TASK-030.md for detailed requirements and implementation decisions.
"""

from .data_loader import (
    load_system_events_data,
    load_commits_data,
    prepare_time_series_data,
)
from .time_series_analyzer import TimeSeriesAnalyzer

__all__ = [
    "load_system_events_data",
    "load_commits_data",
    "prepare_time_series_data",
    "TimeSeriesAnalyzer",
]
