#!/usr/bin/env python3
"""
Create Improved Work Log with Date-Based Matching

This script creates a new work_log.json using a more generous date-based matching strategy
that only looks at the date (not time zones) to match system events with commits.

Usage:
    python create_improved_work_log.py [--system-events-file SYSTEM_EVENTS_FILE] [--commits-file COMMITS_FILE] [--output-file OUTPUT_FILE]
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def generate_date_list(start_date: str, end_date: str) -> List[str]:
    """Generate a list of dates from start_date to end_date.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def load_system_events(file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load system events and group by date.

    Args:
        file_path: Path to system events JSON file

    Returns:
        Dictionary mapping dates to lists of system events
    """
    logger.info(f"Loading system events from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        events = data.get("system_events", [])
        logger.info(f"Loaded {len(events)} system events")

        # Group events by date
        events_by_date = {}
        for event in events:
            date = event.get("date", "unknown")
            if date != "unknown":
                if date not in events_by_date:
                    events_by_date[date] = []
                events_by_date[date].append(event)

        logger.info(f"System events grouped into {len(events_by_date)} unique dates")
        return events_by_date

    except Exception as e:
        logger.error(f"Error loading system events: {e}")
        return {}


def load_commits(file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load commits and group by date.

    Args:
        file_path: Path to commits JSON file

    Returns:
        Dictionary mapping dates to lists of commits
    """
    logger.info(f"Loading commits from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        commits = data.get("commits", [])
        logger.info(f"Loaded {len(commits)} commits")

        # Group commits by date, only include WBSO commits
        commits_by_date = {}
        wbso_commits = [commit for commit in commits if commit.get("is_wbso", False)]
        logger.info(f"Found {len(wbso_commits)} WBSO commits")

        for commit in wbso_commits:
            date = commit.get("date", "unknown")
            if date != "unknown":
                if date not in commits_by_date:
                    commits_by_date[date] = []
                commits_by_date[date].append(commit)

        logger.info(f"WBSO commits grouped into {len(commits_by_date)} unique dates")
        return commits_by_date

    except Exception as e:
        logger.error(f"Error loading commits: {e}")
        return {}


def calculate_work_hours_from_events(events: List[Dict[str, Any]]) -> float:
    """Calculate work hours from system events.

    This is a simplified calculation based on system events.
    In a real implementation, this would analyze login/logout events,
    system uptime, etc.

    Args:
        events: List of system events for a day

    Returns:
        Estimated work hours for the day
    """
    # For now, use a simple heuristic:
    # If there are system events, assume some work was done
    # This is a placeholder - in reality, you'd analyze login/logout patterns

    if not events:
        return 0.0

    # Count different types of events
    login_events = sum(1 for event in events if "logon" in event.get("event_type", "").lower())
    logout_events = sum(1 for event in events if "logoff" in event.get("event_type", "").lower())

    # Simple heuristic: if there are login/logout events, estimate work time
    if login_events > 0 or logout_events > 0:
        # Estimate 4-8 hours based on activity
        return 6.0  # Default to 6 hours if there's activity

    # If there are other system events, assume some work
    return 2.0  # Default to 2 hours for other activity


def create_work_log_records(
    dates: List[str], events_by_date: Dict[str, List[Dict[str, Any]]], commits_by_date: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Create work log records for each date.

    Args:
        dates: List of dates to process
        events_by_date: System events grouped by date
        commits_by_date: Commits grouped by date

    Returns:
        List of work log records
    """
    work_log_records = []

    for date in dates:
        # Get events and commits for this date
        events = events_by_date.get(date, [])
        commits = commits_by_date.get(date, [])

        # Only create a record if there are commits with is_wbso
        if commits:
            work_hours = calculate_work_hours_from_events(events)

            record = {
                "date": date,
                "work_hours": work_hours,
                "commit_count": len(commits),
                "commits": commits,
                "system_events_count": len(events),
                "has_commits": True,
                "has_system_events": len(events) > 0,
            }

            work_log_records.append(record)
            logger.info(f"Created work log record for {date}: {len(commits)} commits, {work_hours:.1f} hours")

    return work_log_records


def create_improved_work_log(system_events_file: Path, commits_file: Path, output_file: Path) -> None:
    """Create improved work log with date-based matching.

    Args:
        system_events_file: Path to system events JSON file
        commits_file: Path to commits JSON file
        output_file: Path to output work log JSON file
    """
    logger.info("Creating improved work log with date-based matching")

    # Generate date list from 2025-06-01 to today
    start_date = "2025-06-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    dates = generate_date_list(start_date, end_date)
    logger.info(f"Processing dates from {start_date} to {end_date} ({len(dates)} days)")

    # Load system events and commits
    events_by_date = load_system_events(system_events_file)
    commits_by_date = load_commits(commits_file)

    # Create work log records
    work_log_records = create_work_log_records(dates, events_by_date, commits_by_date)

    # Create output data
    output_data = {
        "work_log_records": work_log_records,
        "metadata": {
            "total_days": len(dates),
            "days_with_commits": len(work_log_records),
            "total_commits": sum(record["commit_count"] for record in work_log_records),
            "total_work_hours": sum(record["work_hours"] for record in work_log_records),
            "date_range": {"start": start_date, "end": end_date},
            "creation_timestamp": datetime.now().isoformat(),
            "matching_strategy": "date_based",
        },
    }

    # Write output file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully created work log with {len(work_log_records)} records")
        logger.info(f"Total work hours: {output_data['metadata']['total_work_hours']:.1f}")
        logger.info(f"Total commits: {output_data['metadata']['total_commits']}")
        logger.info(f"Days with commits: {output_data['metadata']['days_with_commits']}")
        logger.info(f"Output saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error writing output file: {e}")


def main():
    """Main function to create improved work log."""
    parser = argparse.ArgumentParser(description="Create improved work log with date-based matching strategy")
    parser.add_argument(
        "--system-events-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "all_system_events.json",
        help="System events JSON file (default: docs/project/hours/data/all_system_events.json)",
    )
    parser.add_argument(
        "--commits-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits_processed.json",
        help="Commits JSON file (default: docs/project/hours/data/commits_processed.json)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "work_log.json",
        help="Output work log JSON file (default: docs/project/hours/data/work_log.json)",
    )

    args = parser.parse_args()

    # Create improved work log
    create_improved_work_log(args.system_events_file, args.commits_file, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
