#!/usr/bin/env python3
"""Work Sessions and Commits Integration Script.

This script combines work sessions from system events with git commits to create
a comprehensive work log for WBSO compliance. It implements intelligent assignment
logic and WBSO eligibility promotion.

See docs/technical/WBSO_COMPLIANCE.md for detailed business requirements.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_commit_timestamp(timestamp_str: str) -> datetime:
    """Parse commit timestamp with timezone information.

    Args:
        timestamp_str: ISO 8601 timestamp string (e.g., "2023-05-03T11:38:52+02:00")

    Returns:
        datetime: Parsed datetime object with timezone info

    Raises:
        ValueError: If timestamp format is invalid
    """
    try:
        # Handle ISO 8601 format with timezone
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        logger.error(f"Failed to parse commit timestamp '{timestamp_str}': {e}")
        raise ValueError(f"Failed to parse commit timestamp '{timestamp_str}': {e}")


def parse_work_session_timestamp(timestamp_str: str) -> datetime:
    """Parse work session timestamp in local format.

    Args:
        timestamp_str: Local timestamp string (e.g., "2025-04-27 17:22:37")

    Returns:
        datetime: Parsed datetime object with local timezone

    Raises:
        ValueError: If timestamp format is invalid
    """
    try:
        # Handle local format without timezone - assume local timezone
        naive_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        # Convert to timezone-aware using local timezone
        return naive_dt.replace(tzinfo=timezone.utc)  # Assume UTC for consistency
    except ValueError as e:
        logger.error(f"Failed to parse work session timestamp '{timestamp_str}': {e}")
        raise ValueError(f"Failed to parse work session timestamp '{timestamp_str}': {e}")


def filter_commits_by_date(commits: List[Dict], start_date: str) -> List[Dict]:
    """Filter commits to only include those from start_date onwards.

    Args:
        commits: List of commit dictionaries
        start_date: Start date in YYYY-MM-DD format

    Returns:
        List[Dict]: Filtered commits from start_date onwards
    """
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    filtered_commits = []

    for commit in commits:
        try:
            commit_datetime = parse_commit_timestamp(commit["timestamp"])
            if commit_datetime.date() >= start_datetime.date():
                filtered_commits.append(commit)
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping commit with invalid timestamp: {e}")
            continue

    logger.info(f"Filtered {len(filtered_commits)} commits from {len(commits)} total (from {start_date} onwards)")
    return filtered_commits


def assign_commits_to_sessions(work_sessions: List[Dict], commits: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Assign commits to work sessions based on time range matching.

    Args:
        work_sessions: List of work session dictionaries
        commits: List of commit dictionaries

    Returns:
        Tuple[List[Dict], List[Dict]]: (enhanced_sessions, unassigned_commits)
    """
    enhanced_sessions = []
    unassigned_commits = []
    assigned_commit_hashes = set()

    for session in work_sessions:
        # Parse session timestamps
        try:
            session_start = parse_work_session_timestamp(session["start_time"])
            session_end = parse_work_session_timestamp(session["end_time"])
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping session {session.get('session_id', 'unknown')}: {e}")
            # Create enhanced session with empty assigned_commits for invalid sessions
            enhanced_session = session.copy()
            enhanced_session["assigned_commits"] = []
            enhanced_session["commit_count"] = 0
            enhanced_session["is_wbso"] = False
            enhanced_sessions.append(enhanced_session)
            continue

        # Find commits within session time range
        assigned_commits = []
        session_wbso_eligible = False

        for commit in commits:
            try:
                commit_datetime = parse_commit_timestamp(commit["timestamp"])

                # Check if commit falls within session time range
                if session_start <= commit_datetime <= session_end:
                    assigned_commits.append(commit)
                    assigned_commit_hashes.add(commit["hash"])

                    # Check WBSO eligibility
                    if commit.get("is_wbso", False):
                        session_wbso_eligible = True

            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping commit with invalid data: {e}")
                continue

        # Create enhanced session
        enhanced_session = session.copy()
        enhanced_session["assigned_commits"] = assigned_commits
        enhanced_session["commit_count"] = len(assigned_commits)
        enhanced_session["is_wbso"] = session_wbso_eligible

        enhanced_sessions.append(enhanced_session)

        if assigned_commits:
            logger.info(f"Session {session['session_id']}: assigned {len(assigned_commits)} commits, WBSO: {session_wbso_eligible}")

    # Find unassigned commits
    for commit in commits:
        if commit["hash"] not in assigned_commit_hashes:
            unassigned_commits.append(commit)

    logger.info(f"Assignment complete: {len(assigned_commit_hashes)} commits assigned, {len(unassigned_commits)} unassigned")
    return enhanced_sessions, unassigned_commits


def group_unassigned_commits_by_date(unassigned_commits: List[Dict]) -> Dict[str, Dict]:
    """Group unassigned commits by date for easy review.

    Args:
        unassigned_commits: List of unassigned commit dictionaries

    Returns:
        Dict[str, Dict]: Commits grouped by date with count and commit list
    """
    grouped_commits = {}

    for commit in unassigned_commits:
        try:
            commit_datetime = parse_commit_timestamp(commit["timestamp"])
            date_str = commit_datetime.strftime("%Y-%m-%d")

            if date_str not in grouped_commits:
                grouped_commits[date_str] = {"count": 0, "commits": []}

            grouped_commits[date_str]["commits"].append(commit)
            grouped_commits[date_str]["count"] += 1

        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping commit for grouping: {e}")
            continue

    logger.info(f"Grouped {len(unassigned_commits)} unassigned commits into {len(grouped_commits)} dates")
    return grouped_commits


def calculate_summary_statistics(
    enhanced_sessions: List[Dict], commits: List[Dict], assigned_count: int, unassigned_count: int
) -> Dict[str, Any]:
    """Calculate comprehensive summary statistics.

    Args:
        enhanced_sessions: List of enhanced work sessions
        commits: List of all processed commits
        assigned_count: Number of assigned commits
        unassigned_count: Number of unassigned commits

    Returns:
        Dict[str, Any]: Summary statistics dictionary
    """
    total_sessions = len(enhanced_sessions)
    wbso_sessions = sum(1 for session in enhanced_sessions if session.get("is_wbso", False))

    total_work_hours = sum(session.get("work_hours", 0) for session in enhanced_sessions)
    wbso_work_hours = sum(session.get("work_hours", 0) for session in enhanced_sessions if session.get("is_wbso", False))

    assignment_rate = (assigned_count / len(commits) * 100) if commits else 0

    summary = {
        "total_work_sessions": total_sessions,
        "wbso_eligible_sessions": wbso_sessions,
        "total_work_hours": round(total_work_hours, 2),
        "wbso_work_hours": round(wbso_work_hours, 2),
        "total_commits_processed": len(commits),
        "assigned_commits": assigned_count,
        "unassigned_commits": unassigned_count,
        "assignment_rate": round(assignment_rate, 1),
    }

    logger.info(
        f"Summary: {total_sessions} sessions, {wbso_sessions} WBSO-eligible, "
        f"{total_work_hours:.2f}h total, {wbso_work_hours:.2f}h WBSO, "
        f"{assignment_rate:.1f}% assignment rate"
    )

    return summary


def load_data_files() -> Tuple[Dict, Dict]:
    """Load input data files.

    Returns:
        Tuple[Dict, Dict]: (system_events_data, commits_data)

    Raises:
        FileNotFoundError: If required data files are missing
        json.JSONDecodeError: If JSON files are malformed
    """
    # Define file paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"

    system_events_file = data_dir / "all_system_events_processed.json"
    commits_file = data_dir / "commits_processed.json"

    # Load system events data
    try:
        with open(system_events_file, "r", encoding="utf-8") as f:
            system_events_data = json.load(f)
        logger.info(f"Loaded system events data from {system_events_file}")
    except FileNotFoundError:
        logger.error(f"System events file not found: {system_events_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in system events file: {e}")
        raise

    # Load commits data
    try:
        with open(commits_file, "r", encoding="utf-8") as f:
            commits_data = json.load(f)
        logger.info(f"Loaded commits data from {commits_file}")
    except FileNotFoundError:
        logger.error(f"Commits file not found: {commits_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in commits file: {e}")
        raise

    return system_events_data, commits_data


def main():
    """Main integration function.

    Processes work sessions and commits to create comprehensive work log.
    """
    logger.info("Starting work sessions and commits integration")

    try:
        # Load data files
        system_events_data, commits_data = load_data_files()

        # Extract work sessions (logon_logoff_sessions)
        work_sessions = system_events_data.get("logon_logoff_sessions", [])
        logger.info(f"Found {len(work_sessions)} work sessions")

        # Extract and filter commits
        all_commits = commits_data.get("commits", [])
        filtered_commits = filter_commits_by_date(all_commits, "2025-05-01")

        # Assign commits to work sessions
        enhanced_sessions, unassigned_commits = assign_commits_to_sessions(work_sessions, filtered_commits)

        # Group unassigned commits by date
        grouped_unassigned = group_unassigned_commits_by_date(unassigned_commits)

        # Calculate summary statistics
        assigned_count = len(filtered_commits) - len(unassigned_commits)
        summary = calculate_summary_statistics(enhanced_sessions, filtered_commits, assigned_count, len(unassigned_commits))

        # Create final work log
        work_log = {"work_sessions": enhanced_sessions, "unassigned_commits": grouped_unassigned, "summary": summary}

        # Save work log
        output_file = Path(__file__).parent.parent / "data" / "work_log.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(work_log, f, indent=2, ensure_ascii=False)

        logger.info(f"Work log saved to {output_file}")
        logger.info("Integration completed successfully")

        # Print summary
        print(f"\n=== WORK SESSIONS AND COMMITS INTEGRATION SUMMARY ===")
        print(f"Total work sessions: {summary['total_work_sessions']}")
        print(f"WBSO-eligible sessions: {summary['wbso_eligible_sessions']}")
        print(f"Total work hours: {summary['total_work_hours']}")
        print(f"WBSO work hours: {summary['wbso_work_hours']}")
        print(f"Commits processed: {summary['total_commits_processed']}")
        print(f"Assignment rate: {summary['assignment_rate']}%")
        print(f"Unassigned commits: {summary['unassigned_commits']}")
        print(f"Work log saved to: {output_file}")

    except Exception as e:
        logger.error(f"Integration failed: {e}")
        raise


if __name__ == "__main__":
    main()
