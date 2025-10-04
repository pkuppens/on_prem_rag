#!/usr/bin/env python3
"""
Integration Script for Work Blocks and WBSO Commits

This script integrates system events work blocks with WBSO commits to create
a comprehensive work log for WBSO hours registration.

Usage:
    python integrate_work_blocks_commits.py [--system-events SYSTEM_EVENTS] [--commits COMMITS] [--output OUTPUT]

Output:
    - work_log.json: Comprehensive work log with computer-on records and unassigned commits
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from backend.datetime_utils import parse_datetime_flexible

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# parse_datetime_flexible function is now imported from datetime_utils module


def is_commit_in_work_block(commit_timestamp: str, work_block_start: str, work_block_end: str) -> bool:
    """Check if a commit falls within a work block time range.

    Args:
        commit_timestamp: ISO 8601 commit timestamp
        work_block_start: Work block start time
        work_block_end: Work block end time

    Returns:
        True if commit is within work block time range
    """
    try:
        commit_dt = parse_datetime_flexible(commit_timestamp)
        start_dt = parse_datetime_flexible(work_block_start)
        end_dt = parse_datetime_flexible(work_block_end)

        if not all([commit_dt, start_dt, end_dt]):
            return False

        # Add small buffer (5 minutes) to account for timezone differences
        buffer = timedelta(minutes=5)
        return start_dt - buffer <= commit_dt <= end_dt + buffer

    except Exception as e:
        logger.warning(f"Error checking commit in work block: {e}")
        return False


def integrate_work_blocks_with_commits(system_events_file: Path, commits_file: Path) -> Dict[str, Any]:
    """Integrate system events work blocks with WBSO commits.

    Args:
        system_events_file: Path to system events JSON file
        commits_file: Path to processed commits JSON file

    Returns:
        Integrated work log data structure
    """
    logger.info("Loading system events work blocks...")
    with open(system_events_file, "r", encoding="utf-8") as f:
        system_events_data = json.load(f)

    logger.info("Loading WBSO commits...")
    with open(commits_file, "r", encoding="utf-8") as f:
        commits_data = json.load(f)

    # Get work blocks and WBSO commits
    work_blocks = system_events_data.get("computer_on_sessions", [])
    all_commits = commits_data.get("commits", [])
    wbso_commits = [commit for commit in all_commits if commit.get("is_wbso", False)]

    logger.info(f"Found {len(work_blocks)} work blocks and {len(wbso_commits)} WBSO commits")

    # Process work blocks with commits
    work_log_records = []
    assigned_commit_hashes = set()

    for work_block in work_blocks:
        work_block_id = work_block.get("block_id", "")
        start_time = work_block.get("start_time", "")
        end_time = work_block.get("end_time", "")
        work_hours = work_block.get("work_hours", 0)

        # Find commits within this work block
        commits_in_block = []
        for commit in wbso_commits:
            if is_commit_in_work_block(commit["timestamp"], start_time, end_time):
                commits_in_block.append(commit)
                assigned_commit_hashes.add(commit["hash"])

        # Create work log record
        work_log_record = {
            "work_block_id": work_block_id,
            "start_time": start_time,
            "end_time": end_time,
            "work_hours": work_hours,
            "confidence_score": work_block.get("confidence_score", 0),
            "session_type": work_block.get("session_type", ""),
            "commits": commits_in_block,
            "commit_count": len(commits_in_block),
            "has_commits": len(commits_in_block) > 0,
        }

        work_log_records.append(work_log_record)

    # Find unassigned WBSO commits
    unassigned_commits = [commit for commit in wbso_commits if commit["hash"] not in assigned_commit_hashes]

    # Calculate statistics
    total_work_hours = sum(record["work_hours"] for record in work_log_records if record["has_commits"])
    work_blocks_with_commits = len([record for record in work_log_records if record["has_commits"]])
    total_commits_assigned = len(assigned_commit_hashes)

    # Create final work log structure
    work_log = {
        "work_log_records": work_log_records,
        "unassigned_commits": unassigned_commits,
        "summary": {
            "total_work_blocks": len(work_blocks),
            "work_blocks_with_commits": work_blocks_with_commits,
            "total_work_hours": round(total_work_hours, 2),
            "total_wbso_commits": len(wbso_commits),
            "assigned_commits": total_commits_assigned,
            "unassigned_commits": len(unassigned_commits),
            "assignment_rate": round((total_commits_assigned / len(wbso_commits)) * 100, 1) if wbso_commits else 0,
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "system_events_file": str(system_events_file),
            "commits_file": str(commits_file),
            "integration_version": "1.0",
        },
    }

    return work_log


def main():
    """Main function to integrate work blocks with commits."""
    parser = argparse.ArgumentParser(description="Integrate system events work blocks with WBSO commits for work log generation")
    parser.add_argument(
        "--system-events",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "system_events_20250930.json",
        help="Path to system events JSON file (default: docs/project/hours/data/system_events_20250930.json)",
    )
    parser.add_argument(
        "--commits",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "commits_processed.json",
        help="Path to processed commits JSON file (default: docs/project/hours/data/commits_processed.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "work_log.json",
        help="Output work log JSON file (default: docs/project/hours/data/work_log.json)",
    )

    args = parser.parse_args()

    # Validate input files
    if not args.system_events.exists():
        logger.error(f"System events file does not exist: {args.system_events}")
        return 1

    if not args.commits.exists():
        logger.error(f"Commits file does not exist: {args.commits}")
        return 1

    # Create output directory if it doesn't exist
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Integrate work blocks with commits
    work_log = integrate_work_blocks_with_commits(args.system_events, args.commits)

    # Write work log to file
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(work_log, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully created work log: {args.output}")
        logger.info(
            f"Work blocks with commits: {work_log['summary']['work_blocks_with_commits']}/{work_log['summary']['total_work_blocks']}"
        )
        logger.info(f"Total work hours: {work_log['summary']['total_work_hours']}")
        logger.info(f"Commit assignment rate: {work_log['summary']['assignment_rate']}%")
        logger.info(f"Unassigned commits: {work_log['summary']['unassigned_commits']}")

    except Exception as e:
        logger.error(f"Error writing work log file {args.output}: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
