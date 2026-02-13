#!/usr/bin/env python3
"""
Computer On Events Loader

Loads system events from CSV files and identifies computer-on sessions.

Author: AI Assistant
Created: 2025-11-28
"""

import csv
from pathlib import Path
from typing import Any, Dict, List

from .calendar_event import WBSODataset, WBSOSession
from .logging_config import get_logger
from .time_utils import parse_datetime_flexible

logger = get_logger("computer_on_loader")


def load_system_events_from_csv(csv_file: Path) -> List[Dict[str, Any]]:
    """
    Load system events from CSV file.

    Args:
        csv_file: Path to CSV file

    Returns:
        List of event dictionaries
    """
    events = []

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Handle BOM and malformed header in DateTime column
                datetime_value = ""
                for key, value in row.items():
                    if "DateTime" in key or "datetime" in key.lower():
                        datetime_value = value
                        break

                event = {
                    "datetime": datetime_value,
                    "event_id": row.get("EventId", ""),
                    "event_type": row.get("EventType", ""),
                    "message": row.get("Message", ""),
                    "record_id": row.get("RecordId", ""),
                }
                events.append(event)

        logger.info(f"Loaded {len(events)} system events from {csv_file}")

    except Exception as e:
        logger.error(f"Error loading system events from {csv_file}: {e}")

    return events


def identify_computer_on_sessions(events: List[Dict[str, Any]]) -> List[WBSOSession]:
    """
    Identify computer-on sessions from system events.

    Looks for startup events (EventId 6005 or 6013) and matching shutdown events (EventId 1074).

    Args:
        events: List of event dictionaries

    Returns:
        List of WBSOSession objects
    """
    sessions = []
    session_counter = 1

    # Sort events by datetime
    events_with_dt = []
    for event in events:
        dt = parse_datetime_flexible(event["datetime"])
        if dt:
            events_with_dt.append((dt, event))

    events_with_dt.sort(key=lambda x: x[0])

    i = 0
    while i < len(events_with_dt):
        start_dt, start_event = events_with_dt[i]

        # Look for startup events (EventId 6005 or 6013)
        if start_event["event_id"] in ["6005", "6013"] and (
            "startup" in start_event["message"].lower() or "started" in start_event["message"].lower()
        ):
            session_start = start_dt
            session_date = session_start.date()

            # Look for matching shutdown event (EventId 1074) on the same date
            j = i + 1
            shutdown_found = False

            while j < len(events_with_dt):
                end_dt, end_event = events_with_dt[j]

                # Check if we've moved to next day
                if end_dt.date() > session_date:
                    break

                # Look for shutdown event
                if end_event["event_id"] == "1074" and (
                    "shutdown" in end_event["message"].lower() or "stopped" in end_event["message"].lower()
                ):
                    session_end = end_dt

                    # Ensure same date (no date crossing)
                    if session_end.date() == session_date:
                        shutdown_found = True

                        # Calculate duration
                        duration = session_end - session_start
                        duration_hours = duration.total_seconds() / 3600.0
                        duration_minutes = int(duration.total_seconds() / 60)

                        # Determine session type
                        if duration_hours >= 8:
                            session_type = "full_day"
                        elif duration_hours >= 4:
                            session_type = "half_day"
                        else:
                            session_type = "short_session"

                        # Create WBSOSession
                        session = WBSOSession(
                            session_id=f"cos_{session_counter:03d}",
                            start_time=session_start,
                            end_time=session_end,
                            work_hours=duration_hours,  # Will be adjusted by time polishing
                            duration_hours=duration_hours,
                            date=session_date.isoformat(),
                            session_type=session_type,
                            is_wbso=True,  # All computer-on sessions are WBSO eligible
                            wbso_category="GENERAL_RD",  # Default, will be updated by activity assignment
                            is_synthetic=False,
                            commit_count=0,
                            source_type="real",
                            wbso_justification=f"Computer-on session: {start_event['message']} to {end_event['message']}",
                            has_computer_on=True,
                            is_weekend=session_date.weekday() >= 5,
                        )

                        sessions.append(session)
                        session_counter += 1

                        # Move to next event after shutdown
                        i = j + 1
                        break

                j += 1

            if not shutdown_found:
                i += 1
        else:
            i += 1

    logger.info(f"Identified {len(sessions)} computer-on sessions")
    return sessions


def load_all_computer_on_sessions(data_dir: Path) -> WBSODataset:
    """
    Load all computer-on sessions from system events CSV files.

    Args:
        data_dir: Directory containing system events CSV files

    Returns:
        WBSODataset with all computer-on sessions
    """
    dataset = WBSODataset()

    # Find all system events CSV files
    csv_files = list(data_dir.glob("system_events_*.csv"))

    if not csv_files:
        logger.warning(f"No system events CSV files found in {data_dir}")
        return dataset

    logger.info(f"Found {len(csv_files)} system events CSV files")

    all_events = []
    for csv_file in csv_files:
        events = load_system_events_from_csv(csv_file)
        all_events.extend(events)

    if not all_events:
        logger.warning("No system events loaded")
        return dataset

    # Identify computer-on sessions
    sessions = identify_computer_on_sessions(all_events)
    dataset.sessions = sessions

    logger.info(f"Loaded {len(sessions)} computer-on sessions from {len(all_events)} system events")

    return dataset
