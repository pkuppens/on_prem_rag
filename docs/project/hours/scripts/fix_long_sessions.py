#!/usr/bin/env python3
"""
Fix Long Sessions with Breaks and Clipping Rules

This script processes calendar events to:
1. Inspect sessions longer than 6 hours and add breaks (lunch if >6h, dinner if >11h)
2. Clip sessions to max 10 hours/day and 40 hours/week
3. Recalculate work hours with breaks
4. Regenerate calendar events CSV and summaries

Author: AI Assistant
Created: 2025-12-02
"""

import csv
import json
from pathlib import Path
from datetime import datetime, timedelta, time
from collections import defaultdict
from typing import List, Dict, Any, Tuple
import sys

# Add business layer to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "business"))

from work_session import WorkSession

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "data"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"
CALENDAR_EVENTS_BACKUP = DATA_DIR / "calendar_events_backup.csv"
CALENDAR_EVENTS_FIXED = DATA_DIR / "calendar_events_fixed.csv"
OUTPUT_DIR = SCRIPT_DIR / "output"


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string in ISO format."""
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        # Try alternative formats
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Could not parse datetime: {dt_str}")


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def calculate_hours(start_dt: datetime, end_dt: datetime) -> float:
    """Calculate hours between two datetimes."""
    delta = end_dt - start_dt
    return delta.total_seconds() / 3600.0


def get_iso_week(dt: datetime) -> Tuple[str, int, int]:
    """Get ISO week number, year, and week number."""
    iso_year, iso_week, iso_weekday = dt.isocalendar()
    iso_week_str = f"{iso_year}-W{iso_week:02d}"
    return iso_week_str, iso_year, iso_week


def add_breaks_to_session(start_dt: datetime, end_dt: datetime, current_hours: float) -> Tuple[float, Dict[str, str]]:
    """
    Add breaks to long sessions and return work hours and break info.

    Business Rules:
    - Sessions > 6 hours: Add lunch break (30 min, 12:20-12:50)
    - Sessions > 11 hours: Add both lunch (30 min) and dinner (45 min, 18:10-18:55)
    - Breaks are at polished times

    Args:
        start_dt: Session start datetime
        end_dt: Session end datetime
        current_hours: Current session hours

    Returns:
        Tuple of (work_hours, breaks_dict)
    """
    breaks = {}
    break_minutes = 0

    start_time = start_dt.time()
    end_time = end_dt.time()

    # Check for lunch break (> 6 hours and spans lunch time)
    if current_hours > 6.0:
        lunch_start = time(12, 20)
        lunch_end = time(12, 50)
        # Add lunch if session starts before 10:00 and ends after 14:00
        if start_time < time(10, 0) and end_time > time(14, 0):
            breaks["lunch_break"] = f"{lunch_start.strftime('%H:%M')}-{lunch_end.strftime('%H:%M')}"
            break_minutes += 30

    # Check for dinner break (> 11 hours and spans dinner time)
    if current_hours > 11.0:
        dinner_start = time(18, 10)
        dinner_end = time(18, 55)
        # Add dinner if session starts before 16:00 and ends after 20:00
        if start_time < time(16, 0) and end_time > time(20, 0):
            breaks["dinner_break"] = f"{dinner_start.strftime('%H:%M')}-{dinner_end.strftime('%H:%M')}"
            break_minutes += 45

    # Calculate work hours (total hours minus breaks)
    work_hours = current_hours - (break_minutes / 60.0)

    return work_hours, breaks


def clip_session_to_daily_limit(start_dt: datetime, end_dt: datetime, max_hours_per_day: float = 10.0) -> Tuple[datetime, datetime]:
    """
    Clip session to maximum hours per day.

    Args:
        start_dt: Session start datetime
        end_dt: Session end datetime
        max_hours_per_day: Maximum hours allowed per day (default: 10.0)

    Returns:
        Tuple of (clipped_start, clipped_end)
    """
    current_hours = calculate_hours(start_dt, end_dt)

    if current_hours <= max_hours_per_day:
        return start_dt, end_dt

    # Clip to max hours
    max_duration = timedelta(hours=max_hours_per_day)
    clipped_end = start_dt + max_duration

    return start_dt, clipped_end


def load_calendar_events() -> List[Dict[str, Any]]:
    """Load calendar events from CSV."""
    if not CALENDAR_EVENTS_CSV.exists():
        raise FileNotFoundError(f"Calendar events CSV not found: {CALENDAR_EVENTS_CSV}")

    events = []
    with open(CALENDAR_EVENTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)

    return events


def process_sessions_with_breaks_and_clipping(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process sessions to add breaks and apply clipping rules.

    Args:
        events: List of calendar event dictionaries

    Returns:
        List of processed event dictionaries
    """
    processed_events = []
    daily_hours: Dict[str, float] = defaultdict(float)  # date -> total hours
    weekly_hours: Dict[str, float] = defaultdict(float)  # iso_week -> total hours

    for event in events:
        session_id = event.get("session_id", "")
        start_str = event.get("start_datetime", "")
        end_str = event.get("end_datetime", "")
        date_str = event.get("date", "")
        current_hours = float(event.get("hours", 0.0))

        if not start_str or not end_str:
            processed_events.append(event)
            continue

        try:
            start_dt = parse_datetime(start_str)
            end_dt = parse_datetime(end_str)

            # Get ISO week info
            iso_week_str, iso_year, iso_week = get_iso_week(start_dt)
            if not date_str:
                date_str = start_dt.strftime("%Y-%m-%d")

            # Add breaks for long sessions first
            work_hours, breaks = add_breaks_to_session(start_dt, end_dt, current_hours)

            # Check daily limit (10 hours/day) - use work_hours (after breaks)
            daily_total = daily_hours[date_str]
            if daily_total + work_hours > 10.0:
                # Clip this session to fit within daily limit
                remaining_daily_hours = 10.0 - daily_total
                if remaining_daily_hours > 0:
                    # Adjust end time to fit remaining work hours
                    # Need to account for breaks when calculating end time
                    break_minutes = sum([30 if "lunch" in k else 45 for k in breaks.keys()])
                    total_duration_hours = remaining_daily_hours + (break_minutes / 60.0)
                    max_duration = timedelta(hours=total_duration_hours)
                    end_dt = start_dt + max_duration
                    work_hours = remaining_daily_hours
                    current_hours = total_duration_hours
                else:
                    # Skip this session (day already at limit)
                    print(f"⚠️  Skipping {session_id}: daily limit reached for {date_str}")
                    continue

            # Check weekly limit (40 hours/week) - use work_hours (after breaks)
            weekly_total = weekly_hours[iso_week_str]
            if weekly_total + work_hours > 40.0:
                # Clip this session to fit within weekly limit
                remaining_weekly_hours = 40.0 - weekly_total
                if remaining_weekly_hours > 0:
                    # Adjust end time to fit remaining work hours
                    # Need to account for breaks when calculating end time
                    break_minutes = sum([30 if "lunch" in k else 45 for k in breaks.keys()])
                    total_duration_hours = remaining_weekly_hours + (break_minutes / 60.0)
                    max_duration = timedelta(hours=total_duration_hours)
                    end_dt = start_dt + max_duration
                    work_hours = remaining_weekly_hours
                    current_hours = total_duration_hours
                else:
                    # Skip this session (week already at limit)
                    print(f"⚠️  Skipping {session_id}: weekly limit reached for {iso_week_str}")
                    continue

            # Clip to daily limit after breaks (safety check)
            start_dt, end_dt = clip_session_to_daily_limit(start_dt, end_dt, max_hours_per_day=10.0)

            # Recalculate final work hours (total hours minus breaks)
            final_hours = calculate_hours(start_dt, end_dt)
            break_minutes = sum([30 if "lunch" in k else 45 for k in breaks.keys()])
            work_hours = final_hours - (break_minutes / 60.0)

            # Update event with processed data
            processed_event = event.copy()
            processed_event["start_datetime"] = format_datetime(start_dt)
            processed_event["end_datetime"] = format_datetime(end_dt)
            processed_event["hours"] = f"{work_hours:.2f}"
            processed_event["date"] = date_str
            processed_event["iso_week_number"] = iso_week_str
            processed_event["iso_year"] = str(iso_year)
            processed_event["iso_week"] = str(iso_week)

            # Add break information to description if breaks were added
            if breaks:
                break_info = ", ".join([f"{k}: {v}" for k, v in breaks.items()])
                original_desc = processed_event.get("description", "")
                processed_event["description"] = f"{original_desc} [{break_info}]"

            processed_events.append(processed_event)

            # Update daily and weekly totals
            daily_hours[date_str] += work_hours
            weekly_hours[iso_week_str] += work_hours

            # Log long sessions that were processed
            if current_hours > 6.0:
                print(
                    f"📝 Processed long session {session_id}: {current_hours:.2f}h -> {work_hours:.2f}h "
                    f"(breaks: {breaks if breaks else 'none'})"
                )

        except Exception as e:
            print(f"❌ Error processing session {session_id}: {e}")
            processed_events.append(event)  # Keep original if processing fails

    return processed_events


def save_calendar_events(events: List[Dict[str, Any]], output_file: Path) -> None:
    """Save calendar events to CSV."""
    if not events:
        print("⚠️  No events to save")
        return

    # Get fieldnames from first event
    fieldnames = list(events[0].keys())

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

    print(f"✅ Saved {len(events)} events to {output_file}")


def backup_calendar_events() -> None:
    """Create backup of original calendar events."""
    if CALENDAR_EVENTS_CSV.exists():
        import shutil

        shutil.copy2(CALENDAR_EVENTS_CSV, CALENDAR_EVENTS_BACKUP)
        print(f"✅ Backup created: {CALENDAR_EVENTS_BACKUP}")


def calculate_total_hours(events: List[Dict[str, Any]]) -> float:
    """Calculate total hours from events."""
    total = 0.0
    for event in events:
        try:
            hours = float(event.get("hours", 0.0))
            total += hours
        except (ValueError, TypeError):
            continue
    return total


def main():
    """Main entry point."""
    print("=" * 60)
    print("Fix Long Sessions with Breaks and Clipping Rules")
    print("=" * 60)
    print()

    # Backup original file
    print("Creating backup...")
    backup_calendar_events()

    # Load calendar events
    print(f"Loading calendar events from {CALENDAR_EVENTS_CSV}...")
    events = load_calendar_events()
    print(f"Loaded {len(events)} events")

    # Calculate original total hours
    original_total = calculate_total_hours(events)
    print(f"Original total hours: {original_total:.2f}")
    print()

    # Process sessions
    print("Processing sessions (adding breaks, applying clipping rules)...")
    processed_events = process_sessions_with_breaks_and_clipping(events)
    print(f"Processed {len(processed_events)} events")
    print()

    # Calculate new total hours
    new_total = calculate_total_hours(processed_events)
    print(f"New total hours: {new_total:.2f}")
    print(f"Reduction: {original_total - new_total:.2f} hours ({((original_total - new_total) / original_total * 100):.1f}%)")
    print()

    # Save fixed events
    print(f"Saving fixed events to {CALENDAR_EVENTS_FIXED}...")
    save_calendar_events(processed_events, CALENDAR_EVENTS_FIXED)

    print()
    print("=" * 60)
    print("✅ Processing complete!")
    print("=" * 60)
    print()
    print(f"Next steps:")
    print(f"1. Review fixed events in: {CALENDAR_EVENTS_FIXED}")
    print(f"2. If total hours > 750, replace original file and regenerate summaries")
    print(f"3. Run: python scripts/generate_weekly_summary.py")
    print()

    if new_total > 750.0:
        print(f"✅ Total hours ({new_total:.2f}) exceeds 750 - ready for commit and calendar update")
    else:
        print(f"⚠️  Total hours ({new_total:.2f}) is below 750 - review needed")


if __name__ == "__main__":
    main()
