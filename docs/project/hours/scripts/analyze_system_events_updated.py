#!/usr/bin/env python3
"""
Updated System Events Computer-On Session Analysis Script

This script analyzes the consolidated system events CSV file to identify computer-on sessions
and extracts date fields for improved matching with commits.

Usage:
    python analyze_system_events_updated.py [--input-file INPUT_FILE] [--output-file OUTPUT_FILE]
"""

import csv
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class SystemEvent:
    """Represents a single system event from the CSV file."""

    datetime: str
    event_id: str
    log_name: str
    event_type: str
    level: str
    username: str
    process_name: str
    message: str
    additional_info: str
    record_id: str
    date: str  # Extracted date field


@dataclass
class ComputerOnSession:
    """Represents a computer-on session with work hours calculation."""

    block_id: str
    start_time: str
    end_time: str
    duration_hours: float
    confidence_score: float
    evidence: List[str]
    session_type: str
    work_hours: float
    lunch_break: Optional[str]
    dinner_break: Optional[str]
    date: str  # Extracted date field


def parse_datetime_flexible(dt_str: str) -> Optional[datetime]:
    """Parse datetime string with multiple format support."""
    formats = [
        "%Y/%m/%d %H:%M:%S",  # 2025/06/24 07:30:54
        "%m/%d/%Y %I:%M:%S %p",  # 4/27/2025 9:21:21 AM
        "%Y-%m-%d %H:%M:%S",  # 2025-06-24 07:30:54
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse datetime: {dt_str}")
    return None


def extract_date_from_datetime(dt_str: str) -> str:
    """Extract date (YYYY-MM-DD) from datetime string."""
    dt = parse_datetime_flexible(dt_str)
    if dt:
        return dt.strftime("%Y-%m-%d")
    return ""


def load_system_events(input_file: Path) -> List[SystemEvent]:
    """Load system events from CSV file."""
    events = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                event = SystemEvent(
                    datetime=row.get("DateTime", ""),
                    event_id=row.get("EventId", ""),
                    log_name=row.get("LogName", ""),
                    event_type=row.get("EventType", ""),
                    level=row.get("Level", ""),
                    username=row.get("Username", ""),
                    process_name=row.get("ProcessName", ""),
                    message=row.get("Message", ""),
                    additional_info=row.get("AdditionalInfo", ""),
                    record_id=row.get("RecordId", ""),
                    date=extract_date_from_datetime(row.get("DateTime", "")),
                )
                events.append(event)

        logger.info(f"Loaded {len(events)} system events from {input_file}")

    except Exception as e:
        logger.error(f"Error loading system events from {input_file}: {e}")

    return events


def identify_computer_on_sessions(events: List[SystemEvent]) -> List[ComputerOnSession]:
    """Identify computer-on sessions from system events."""
    sessions = []
    session_counter = 1

    # Sort events by datetime
    events.sort(key=lambda x: parse_datetime_flexible(x.datetime) or datetime.min)

    i = 0
    while i < len(events):
        event = events[i]

        # Look for startup events (EventId 6005 or 6013)
        if event.event_id in ["6005", "6013"] and "startup" in event.message.lower():
            session_start = event.datetime
            session_date = event.date

            # Look for corresponding shutdown event
            j = i + 1
            shutdown_event = None

            while j < len(events):
                next_event = events[j]

                # Check if we've moved to a different date (day boundary)
                if next_event.date != session_date:
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

                    # Determine session type and work hours
                    if duration_hours > 12:
                        session_type = "full_day"
                        work_hours = duration_hours - 1.0  # Subtract 1 hour for lunch
                        lunch_break = "12:00:00"
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

                    # Create session
                    session = ComputerOnSession(
                        block_id=f"cos_{session_counter:03d}",
                        start_time=session_start,
                        end_time=session_end,
                        duration_hours=duration_hours,
                        confidence_score=1.0,
                        evidence=[f"startup_event_{event.event_id}", f"shutdown_event_{shutdown_event.event_id}"],
                        session_type=session_type,
                        work_hours=work_hours,
                        lunch_break=lunch_break,
                        dinner_break=dinner_break,
                        date=session_date,
                    )

                    sessions.append(session)
                    session_counter += 1

                    # Move to next event after shutdown
                    i = j + 1
                    continue

        i += 1

    logger.info(f"Identified {len(sessions)} computer-on sessions")
    return sessions


def save_sessions_to_json(sessions: List[ComputerOnSession], output_file: Path) -> None:
    """Save computer-on sessions to JSON file."""
    output_data = {
        "file_analyzed": str(output_file),
        "total_events": len(sessions),
        "computer_on_sessions": [asdict(session) for session in sessions],
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "date_range": {
                "start": min(session.date for session in sessions) if sessions else None,
                "end": max(session.date for session in sessions) if sessions else None,
            },
        },
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully saved {len(sessions)} sessions to {output_file}")

    except Exception as e:
        logger.error(f"Error saving sessions to {output_file}: {e}")


def main():
    """Main function to analyze system events."""
    parser = argparse.ArgumentParser(description="Analyze consolidated system events to identify computer-on sessions")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "all_system_events.csv",
        help="Input consolidated system events CSV file (default: docs/project/hours/data/all_system_events.csv)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "all_system_events.json",
        help="Output JSON file for computer-on sessions (default: docs/project/hours/data/all_system_events.json)",
    )

    args = parser.parse_args()

    # Validate input file
    if not args.input_file.exists():
        logger.error(f"Input file does not exist: {args.input_file}")
        return 1

    # Create output directory if it doesn't exist
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load system events
    events = load_system_events(args.input_file)
    if not events:
        logger.error("No system events loaded")
        return 1

    # Identify computer-on sessions
    sessions = identify_computer_on_sessions(events)

    # Save to JSON
    save_sessions_to_json(sessions, args.output_file)

    return 0


if __name__ == "__main__":
    exit(main())
