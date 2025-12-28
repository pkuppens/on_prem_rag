#!/usr/bin/env python3
"""
Fix Hours Calculation in Calendar Events CSV

Recalculates hours from start_datetime and end_datetime for all records,
fixing negative hours and incorrect calculations.

Author: AI Assistant
Created: 2025-01-19
"""

import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Output path in version-controlled directory
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "project" / "hours" / "data"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"


def calculate_hours_from_datetime(start_dt_str: str, end_dt_str: str) -> float:
    """
    Calculate hours from start and end datetime strings.

    Handles timezone issues and 23:59:59 end-of-day sentinel values.

    Args:
        start_dt_str: Start datetime string (ISO format)
        end_dt_str: End datetime string (ISO format)

    Returns:
        Hours as float
    """
    if not start_dt_str or not end_dt_str:
        return 0.0

    try:
        # Parse datetimes - handle timezone info
        # The datetimes in the CSV are in format: 2025-06-15T22:10:00 (no timezone)
        # Remove timezone suffix if present for consistent parsing
        start_dt_str_clean = start_dt_str.replace("Z", "").split("+")[0]
        end_dt_str_clean = end_dt_str.replace("Z", "").split("+")[0]

        # Parse as naive datetimes (assume same timezone - Europe/Amsterdam)
        start_dt = datetime.fromisoformat(start_dt_str_clean)
        end_dt = datetime.fromisoformat(end_dt_str_clean)

        # If end time is 23:59:59, it's a sentinel value meaning "end of day"
        # Calculate duration normally - it should be positive for same-day events
        duration = end_dt - start_dt
        hours = duration.total_seconds() / 3600.0

        # If negative, it might be a timezone issue or cross-day event
        # For same-day events, recalculate using time components only
        if hours < 0:
            start_date = start_dt.date()
            end_date = end_dt.date()

            if start_date == end_date:
                # Same day - calculate from time components directly
                start_time = start_dt.time()
                end_time = end_dt.time()

                # Calculate seconds from midnight
                start_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
                end_seconds = end_time.hour * 3600 + end_time.minute * 60 + end_time.second

                # If end is 23:59:59, treat as end of day (24:00:00 = 86400 seconds)
                if end_time.hour == 23 and end_time.minute == 59 and end_time.second == 59:
                    end_seconds = 24 * 3600  # End of day

                if end_seconds >= start_seconds:
                    hours = (end_seconds - start_seconds) / 3600.0
                else:
                    # Shouldn't happen for same-day events
                    hours = 0.0
            else:
                # Cross-day event - use datetime difference but ensure positive
                # This handles cases where timezone conversion caused issues
                hours = abs(hours)

        return max(0.0, hours)  # Ensure non-negative

    except Exception as e:
        print(f"Error calculating hours for {start_dt_str} to {end_dt_str}: {e}")
        return 0.0


def fix_calendar_events_csv(input_path: Path = None, output_path: Path = None) -> None:
    """
    Fix hours calculation in calendar events CSV.

    Args:
        input_path: Input CSV path (uses default if None)
        output_path: Output CSV path (overwrites input if None)
    """
    input_path = input_path or CALENDAR_EVENTS_CSV
    output_path = output_path or input_path

    if not input_path.exists():
        print(f"Error: CSV file not found: {input_path}")
        return

    # Read CSV
    rows: List[Dict[str, str]] = []
    with open(input_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("Error: CSV file has no headers")
            return

        for row in reader:
            # Recalculate hours from datetime
            start_dt_str = row.get("start_datetime", "")
            end_dt_str = row.get("end_datetime", "")
            old_hours = row.get("hours", "0.0")

            # Calculate correct hours
            new_hours = calculate_hours_from_datetime(start_dt_str, end_dt_str)

            # Update hours
            row["hours"] = f"{new_hours:.2f}"

            # Log if hours changed
            try:
                old_hours_float = float(old_hours)
                if abs(old_hours_float - new_hours) > 0.01:  # Significant difference
                    print(
                        f"Fixed hours for {row.get('session_id', 'unknown')}: "
                        f"{old_hours} -> {new_hours:.2f} "
                        f"({start_dt_str} to {end_dt_str})"
                    )
            except (ValueError, TypeError):
                pass

            rows.append(row)

    # Write corrected CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Calculate total hours
    total_hours = sum(float(r["hours"]) for r in rows)
    print(f"\nFixed {len(rows)} records in {output_path}")
    print(f"Total hours: {total_hours:.2f}")


if __name__ == "__main__":
    fix_calendar_events_csv()
