#!/usr/bin/env python3
"""
Process All System Events for Computer-On Session Analysis

This script processes the complete all_system_events.csv file to identify computer-on sessions
according to established criteria: no date crossing, proper startup/shutdown matching,
and break calculations.

Usage:
    python process_all_system_events.py [--input-file INPUT_FILE] [--output-file OUTPUT_FILE]
"""

import csv
import json
import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Add business layer to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "business"))

from work_session import WorkSession
from system_event import SystemEvent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# SystemEvent and WorkSession classes are now imported from business layer


def parse_datetime_flexible(dt_str: str) -> Optional[datetime]:
    """Parse datetime string with multiple format support.

    Args:
        dt_str: DateTime string in various formats

    Returns:
        datetime object or None if parsing fails
    """
    if not dt_str or dt_str.strip() == "":
        return None

    # Clean the datetime string
    clean_datetime = dt_str.strip()
    if clean_datetime.startswith('"'):
        clean_datetime = clean_datetime[1:]
    if clean_datetime.endswith('"'):
        clean_datetime = clean_datetime[:-1]
    # Remove BOM if present
    if clean_datetime.startswith("\ufeff"):
        clean_datetime = clean_datetime[1:]

    if not clean_datetime:
        return None

    formats = [
        "%Y/%m/%d %H:%M:%S",  # 2025/06/24 07:30:54
        "%m/%d/%Y %I:%M:%S %p",  # 4/27/2025 9:21:21 AM
        "%Y-%m-%d %H:%M:%S",  # 2025-06-24 07:30:54
        "%Y-%m-%dT%H:%M:%S",  # 2025-06-24T07:30:54
    ]

    for fmt in formats:
        try:
            return datetime.strptime(clean_datetime, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse datetime: {dt_str}")
    return None


def extract_date_from_datetime(dt_str: str) -> str:
    """Extract date (YYYY-MM-DD) from datetime string.

    Args:
        dt_str: DateTime string in various formats

    Returns:
        Date string in YYYY-MM-DD format or empty string if parsing fails
    """
    dt = parse_datetime_flexible(dt_str)
    if dt:
        return dt.strftime("%Y-%m-%d")
    return ""


def load_system_events(input_file: Path) -> List[SystemEvent]:
    """Load system events from CSV file.

    Args:
        input_file: Path to the CSV file containing system events

    Returns:
        List of SystemEvent objects
    """
    events = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Handle the BOM and malformed header in the DateTime column
                datetime_value = ""
                for key, value in row.items():
                    if "DateTime" in key or "datetime" in key.lower():
                        datetime_value = value
                        break

                event = SystemEvent(
                    datetime=datetime_value,
                    event_id=row.get("EventId", ""),
                    log_name=row.get("LogName", ""),
                    event_type=row.get("EventType", ""),
                    level=row.get("Level", ""),
                    username=row.get("Username", ""),
                    process_name=row.get("ProcessName", ""),
                    message=row.get("Message", ""),
                    additional_info=row.get("AdditionalInfo", ""),
                    record_id=row.get("RecordId", ""),
                    date=extract_date_from_datetime(datetime_value),
                )
                events.append(event)

        logger.info(f"Loaded {len(events)} system events from {input_file}")

    except Exception as e:
        logger.error(f"Error loading system events from {input_file}: {e}")

    return events


def identify_computer_on_sessions(events: List[SystemEvent]) -> List[WorkSession]:
    """Identify computer-on sessions from system events.

    This function implements the established criteria:
    - No date crossing (sessions must start and end on the same date)
    - Proper startup/shutdown event matching
    - Break calculations for different session types

    Args:
        events: List of system events sorted by datetime

    Returns:
        List of WorkSession objects
    """
    sessions = []
    session_counter = 1

    # Sort events by datetime
    events.sort(key=lambda x: parse_datetime_flexible(x.datetime) or datetime.min)

    i = 0
    while i < len(events):
        event = events[i]

        # Look for startup events (EventId 6005 or 6013)
        if event.event_id in ["6005", "6013"] and ("startup" in event.message.lower() or "started" in event.message.lower()):
            session_start = event.datetime
            session_date = event.date

            # Look for corresponding shutdown event
            j = i + 1
            shutdown_event = None

            while j < len(events):
                next_event = events[j]

                # Check if we've moved to a different date (day boundary)
                # This enforces the "no date crossing" criteria
                if next_event.date != session_date:
                    logger.debug(f"Session crosses date boundary: {session_date} -> {next_event.date}")
                    break

                # Look for shutdown events (EventId 1074)
                if next_event.event_id == "1074" and "shutdown" in next_event.message.lower():
                    shutdown_event = next_event
                    break

                j += 1

            if shutdown_event:
                session_end = shutdown_event.datetime

                # Calculate duration
                start_dt = parse_datetime_flexible(session_start)
                end_dt = parse_datetime_flexible(session_end)

                if start_dt and end_dt:
                    duration = end_dt - start_dt
                    duration_hours = duration.total_seconds() / 3600

                    # Determine session type and work hours based on duration
                    if duration_hours > 12:
                        session_type = "full_day"
                        work_hours = duration_hours - 1.0  # Subtract 1 hour for lunch
                        lunch_break = f"{session_date} 12:00:00"
                        dinner_break = None
                    elif duration_hours > 4:
                        session_type = "half_day"
                        work_hours = duration_hours - 0.5  # Subtract 30 min for break
                        lunch_break = None
                        dinner_break = None
                    else:
                        session_type = "short_session"
                        work_hours = duration_hours
                        lunch_break = None
                        dinner_break = None

                    # Calculate duration in minutes for WorkSession
                    duration_minutes = int(duration.total_seconds() / 60)
                    work_duration_minutes = int((work_hours * 60))

                    # Create session using WorkSession business model
                    session = WorkSession(
                        session_id=f"session_{session_counter:03d}",
                        start_time=session_start,
                        end_time=session_end,
                        total_duration_minutes=duration_minutes,
                        work_duration_minutes=work_duration_minutes,
                        date=session_date,
                        crosses_midnight=False,  # We enforce no date crossing
                        block_id=f"cos_{session_counter:03d}",
                        duration_hours=duration_hours,
                        confidence_score=1.0,
                        evidence=[f"startup_event_{event.event_id}", f"shutdown_event_{shutdown_event.event_id}"],
                        session_type=session_type,
                        work_hours=work_hours,
                        lunch_break=lunch_break,
                        dinner_break=dinner_break,
                    )

                    sessions.append(session)
                    session_counter += 1

                    logger.info(
                        f"Identified session {session.block_id}: {session_date} ({session.session_type}, {session.work_hours:.2f}h)"
                    )

                    # Move to next event after shutdown
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1

    logger.info(f"Identified {len(sessions)} computer-on sessions")
    return sessions


def create_processed_system_events_file(input_file: Path, output_file: Path) -> None:
    """Create processed system events file with computer-on sessions.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output JSON file
    """
    logger.info(f"Processing system events from: {input_file}")

    # Load system events
    events = load_system_events(input_file)

    if not events:
        logger.error("No system events loaded. Exiting.")
        return

    # Identify computer-on sessions
    sessions = identify_computer_on_sessions(events)

    # Create output data structure
    output_data = {
        "file_analyzed": str(input_file),
        "total_events": len(events),
        "computer_on_sessions": [session.to_dict() for session in sessions],
        "analysis_metadata": {
            "analysis_date": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "criteria_applied": [
                "No date crossing - sessions must start and end on same date",
                "Startup/shutdown event matching (EventId 6005/6013 -> 1074)",
                "Break calculations: full_day (-1h lunch), half_day (-30min), short_session (no break)",
            ],
        },
    }

    # Write output file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully created processed system events file: {output_file}")
        logger.info(f"Total sessions identified: {len(sessions)}")

        # Print summary statistics
        session_types = {}
        total_work_hours = 0
        for session in sessions:
            session_type = session.session_type
            session_types[session_type] = session_types.get(session_type, 0) + 1
            total_work_hours += session.work_hours

        logger.info("Session type summary:")
        for session_type, count in session_types.items():
            logger.info(f"  {session_type}: {count} sessions")
        logger.info(f"Total work hours: {total_work_hours:.2f}")

    except Exception as e:
        logger.error(f"Error writing output file {output_file}: {e}")


def main():
    """Main function to process command line arguments and run analysis."""
    parser = argparse.ArgumentParser(description="Process all system events for computer-on session analysis")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path("docs/project/hours/data/all_system_events.csv"),
        help="Input CSV file with system events (default: docs/project/hours/data/all_system_events.csv)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("docs/project/hours/data/all_processed_system_events.json"),
        help="Output JSON file with processed sessions (default: docs/project/hours/data/all_processed_system_events.json)",
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input_file.exists():
        logger.error(f"Input file does not exist: {args.input_file}")
        return 1

    # Create output directory if it doesn't exist
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # Process the system events
    create_processed_system_events_file(args.input_file, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
