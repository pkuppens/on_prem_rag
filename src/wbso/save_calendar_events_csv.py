#!/usr/bin/env python3
"""
Save Calendar Events to CSV

Saves calendar events to CSV file with week numbers and hours for reporting.
File is saved in version-controlled directory (not .gitignored).

Author: AI Assistant
Created: 2025-11-30
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .calendar_event import CalendarEvent
from .logging_config import get_logger

logger = get_logger("save_calendar_events_csv")

# Output path in version-controlled directory
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "data"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"


def save_calendar_events_csv(
    events: List[CalendarEvent],
    output_path: Optional[Path] = None,
) -> Path:
    """
    Save calendar events to CSV with week numbers and hours.

    Args:
        events: List of CalendarEvent objects
        output_path: Output CSV path (uses default if None)

    Returns:
        Path to generated CSV file
    """
    output_path = output_path or CALENDAR_EVENTS_CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare rows
    rows = []
    for event in events:
        # Extract start/end times
        start_dt_str = event.start.get("dateTime", "")
        end_dt_str = event.end.get("dateTime", "")

        # Parse datetimes
        start_dt = None
        end_dt = None
        if start_dt_str:
            try:
                start_dt = datetime.fromisoformat(start_dt_str.replace("Z", "+00:00"))
            except:
                pass
        if end_dt_str:
            try:
                end_dt = datetime.fromisoformat(end_dt_str.replace("Z", "+00:00"))
            except:
                pass

        # Calculate hours from datetime difference
        # Always calculate from actual datetime, not from extended properties
        # Extended properties may contain incorrect values (e.g., negative hours)
        hours = 0.0
        if start_dt and end_dt:
            # Handle timezone-aware datetimes correctly
            # If both are timezone-aware, ensure they're in the same timezone
            if start_dt.tzinfo and end_dt.tzinfo:
                # Both timezone-aware, calculate directly
                duration = end_dt - start_dt
            elif start_dt.tzinfo or end_dt.tzinfo:
                # One is timezone-aware, make both naive for calculation
                start_dt_naive = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
                end_dt_naive = end_dt.replace(tzinfo=None) if end_dt.tzinfo else end_dt
                duration = end_dt_naive - start_dt_naive
            else:
                # Both naive, calculate directly
                duration = end_dt - start_dt

            hours = duration.total_seconds() / 3600.0

            # Ensure hours is non-negative (should never be negative for valid events)
            if hours < 0:
                logger.warning(
                    f"Negative hours calculated for event {event.summary}: "
                    f"{start_dt_str} to {end_dt_str} = {hours:.2f} hours. "
                    f"Using calculated value from datetime."
                )
                # For negative hours, try to use work_hours from extended properties as fallback
                if event.extended_properties and "private" in event.extended_properties:
                    work_hours_str = event.extended_properties["private"].get("work_hours")
                    if work_hours_str:
                        try:
                            fallback_hours = float(work_hours_str)
                            if fallback_hours > 0:
                                logger.info(f"Using fallback work_hours: {fallback_hours:.2f}")
                                hours = fallback_hours
                        except (ValueError, TypeError):
                            pass

        # Use calculated hours (never use extended properties work_hours if calculated is valid)
        work_hours = hours

        # Get ISO week number
        iso_week_number = ""
        iso_year = ""
        iso_week = ""
        if event.extended_properties and "private" in event.extended_properties:
            iso_week_number = event.extended_properties["private"].get("iso_week_number", "")
            iso_year = event.extended_properties["private"].get("iso_year", "")
            iso_week = event.extended_properties["private"].get("iso_week", "")

        # Get session ID if available
        session_id = ""
        if event.extended_properties and "private" in event.extended_properties:
            session_id = event.extended_properties["private"].get("session_id", "")

        row = {
            "session_id": session_id,
            "summary": event.summary or "",
            "start_datetime": start_dt_str,
            "end_datetime": end_dt_str,
            "date": start_dt.date().isoformat() if start_dt else "",
            "hours": f"{work_hours:.2f}",
            "iso_week_number": iso_week_number,
            "iso_year": iso_year,
            "iso_week": iso_week,
            "location": event.location or "",
            "description": event.description or "",
        }
        rows.append(row)

    # Write CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "session_id",
            "summary",
            "start_datetime",
            "end_datetime",
            "date",
            "hours",
            "iso_week_number",
            "iso_year",
            "iso_week",
            "location",
            "description",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_hours = sum(float(r["hours"]) for r in rows)
    logger.info(f"Saved {len(rows)} calendar events to {output_path} (total: {total_hours:.2f} hours)")
    return output_path
