#!/usr/bin/env python3
"""
Integrate Work Sessions with Work Logs

This script integrates the WorkSession data from processed system events
with the work log data to create enhanced work logs that include
session information and more accurate work hours.

Usage:
    python integrate_work_sessions.py [--sessions-file SESSIONS_FILE] [--work-log-file WORK_LOG_FILE] [--output-file OUTPUT_FILE]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add business layer to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "business"))

from work_session import WorkSession

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_work_sessions(file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load work sessions and group by date.

    Args:
        file_path: Path to processed system events JSON file

    Returns:
        Dictionary mapping dates to lists of work sessions
    """
    logger.info(f"Loading work sessions from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sessions = data.get("computer_on_sessions", [])
        logger.info(f"Loaded {len(sessions)} work sessions")

        # Group sessions by date
        sessions_by_date = {}
        for session_data in sessions:
            date = session_data.get("date", "unknown")
            if date != "unknown":
                if date not in sessions_by_date:
                    sessions_by_date[date] = []
                sessions_by_date[date].append(session_data)

        logger.info(f"Work sessions grouped into {len(sessions_by_date)} unique dates")
        return sessions_by_date

    except Exception as e:
        logger.error(f"Error loading work sessions: {e}")
        return {}


def load_work_log(file_path: Path) -> Dict[str, Any]:
    """Load work log data.

    Args:
        file_path: Path to work log JSON file

    Returns:
        Work log data dictionary
    """
    logger.info(f"Loading work log from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded work log with {len(data.get('work_log_records', []))} records")
        return data

    except Exception as e:
        logger.error(f"Error loading work log: {e}")
        return {}


def integrate_sessions_with_work_log(
    sessions_by_date: Dict[str, List[Dict[str, Any]]], work_log_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Integrate work sessions with work log data.

    Args:
        sessions_by_date: Work sessions grouped by date
        work_log_data: Work log data

    Returns:
        Enhanced work log data with session information
    """
    logger.info("Integrating work sessions with work log data")

    enhanced_records = []
    total_session_hours = 0
    total_enhanced_hours = 0

    for record in work_log_data.get("work_log_records", []):
        date = record.get("date")
        original_hours = record.get("work_hours", 0)

        # Find matching sessions for this date
        sessions = sessions_by_date.get(date, [])

        if sessions:
            # Calculate total session hours for this date
            session_hours = sum(session.get("work_hours", 0) for session in sessions)
            total_session_hours += session_hours

            # Use session hours if available, otherwise keep original
            enhanced_hours = session_hours if session_hours > 0 else original_hours
            total_enhanced_hours += enhanced_hours

            # Add session information to the record
            enhanced_record = record.copy()
            enhanced_record["work_hours"] = enhanced_hours
            enhanced_record["session_hours"] = session_hours
            enhanced_record["original_hours"] = original_hours
            enhanced_record["sessions"] = sessions
            enhanced_record["session_count"] = len(sessions)

            logger.info(f"Enhanced {date}: {original_hours:.1f}h -> {enhanced_hours:.1f}h ({len(sessions)} sessions)")
        else:
            # No sessions found, keep original data
            enhanced_record = record.copy()
            enhanced_record["session_hours"] = 0
            enhanced_record["original_hours"] = original_hours
            enhanced_record["sessions"] = []
            enhanced_record["session_count"] = 0

            total_enhanced_hours += original_hours

        enhanced_records.append(enhanced_record)

    # Create enhanced work log data
    enhanced_data = work_log_data.copy()
    enhanced_data["work_log_records"] = enhanced_records

    # Add integration metadata
    enhanced_data["integration_metadata"] = {
        "integration_date": datetime.now().isoformat(),
        "total_session_hours": total_session_hours,
        "total_enhanced_hours": total_enhanced_hours,
        "sessions_processed": len(sessions_by_date),
        "records_enhanced": len(enhanced_records),
    }

    logger.info(f"Integration complete: {total_session_hours:.1f}h from sessions, {total_enhanced_hours:.1f}h total")

    return enhanced_data


def main():
    """Main function to integrate work sessions with work logs."""
    parser = argparse.ArgumentParser(description="Integrate WorkSession data with work log data")
    parser.add_argument(
        "--sessions-file",
        type=Path,
        default=Path("docs/project/hours/data/all_processed_system_events.json"),
        help="Processed system events JSON file with WorkSession data (default: docs/project/hours/data/all_processed_system_events.json)",
    )
    parser.add_argument(
        "--work-log-file",
        type=Path,
        default=Path("docs/project/hours/data/work_log_new.json"),
        help="Work log JSON file (default: docs/project/hours/data/work_log_new.json)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("docs/project/hours/data/work_log_enhanced.json"),
        help="Output enhanced work log JSON file (default: docs/project/hours/data/work_log_enhanced.json)",
    )

    args = parser.parse_args()

    # Validate input files
    if not args.sessions_file.exists():
        logger.error(f"Sessions file does not exist: {args.sessions_file}")
        return 1

    if not args.work_log_file.exists():
        logger.error(f"Work log file does not exist: {args.work_log_file}")
        return 1

    # Create output directory if it doesn't exist
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    sessions_by_date = load_work_sessions(args.sessions_file)
    work_log_data = load_work_log(args.work_log_file)

    if not sessions_by_date and not work_log_data:
        logger.error("No data loaded. Exiting.")
        return 1

    # Integrate sessions with work log
    enhanced_data = integrate_sessions_with_work_log(sessions_by_date, work_log_data)

    # Save enhanced work log
    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Enhanced work log saved to: {args.output_file}")

        # Print summary
        metadata = enhanced_data.get("integration_metadata", {})
        logger.info("Integration Summary:")
        logger.info(f"  Sessions processed: {metadata.get('sessions_processed', 0)}")
        logger.info(f"  Records enhanced: {metadata.get('records_enhanced', 0)}")
        logger.info(f"  Total session hours: {metadata.get('total_session_hours', 0):.1f}")
        logger.info(f"  Total enhanced hours: {metadata.get('total_enhanced_hours', 0):.1f}")

    except Exception as e:
        logger.error(f"Error saving enhanced work log: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
