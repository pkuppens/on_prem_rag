#!/usr/bin/env python3
"""
Fix Long Sessions with Breaks and Clipping Rules

This script processes calendar events to:
1. Split sessions longer than 6 hours at break times (lunch if >6h, dinner if >11h)
2. Clip sessions to max 10 hours/day and 40 hours/week
3. Recalculate work hours
4. Regenerate calendar events CSV and summaries

Author: AI Assistant
Created: 2025-12-02
Updated: 2025-12-02
"""

import csv
import hashlib
from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

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


def get_pseudorandom_variation(session_id: str, break_type: str) -> int:
    """
    Get pseudorandom 5-minute variation (0, 1, or 2 steps = 0, 5, or 10 minutes).

    Uses session_id and break_type to generate deterministic but varied offset.

    Args:
        session_id: Session identifier for deterministic variation
        break_type: Type of break ("lunch" or "dinner")

    Returns:
        Number of 5-minute steps (0, 1, or 2)
    """
    # Create deterministic hash from session_id and break_type
    hash_input = f"{session_id}_{break_type}".encode("utf-8")
    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
    # Get 0, 1, or 2 (3 possible values)
    return hash_value % 3


def determine_break_times(start_dt: datetime, end_dt: datetime, current_hours: float, session_id: str) -> List[Dict[str, Any]]:
    """
    Determine break times for long sessions and return list of break periods.

    Business Rules:
    - Sessions > 6 hours: Add lunch break (30 min, base 12:20-12:50)
    - Sessions > 11 hours: Add both lunch (30 min) and dinner (45 min, base 18:10-18:55)
    - Breaks have pseudorandom 5-minute variations (0, 5, or 10 minutes)

    Args:
        start_dt: Session start datetime
        end_dt: Session end datetime
        current_hours: Current session hours
        session_id: Session identifier for pseudorandom variation

    Returns:
        List of break dictionaries with start, end, and type
    """
    breaks = []
    start_time = start_dt.time()
    end_time = end_dt.time()

    # Check for lunch break (> 6 hours and spans lunch time)
    if current_hours > 6.0:
        if start_time < time(10, 0) and end_time > time(14, 0):
            # Get pseudorandom variation (0, 5, or 10 minutes)
            variation_minutes = get_pseudorandom_variation(session_id, "lunch") * 5
            # Use timedelta to handle minute overflow correctly
            base_lunch_start = datetime.combine(start_dt.date(), time(12, 20))
            lunch_start_dt = base_lunch_start + timedelta(minutes=variation_minutes)
            lunch_end_dt = lunch_start_dt + timedelta(minutes=30)
            lunch_start = lunch_start_dt.time()
            lunch_end = lunch_end_dt.time()

            breaks.append(
                {
                    "type": "lunch",
                    "start": lunch_start,
                    "end": lunch_end,
                    "start_dt": lunch_start_dt,
                    "end_dt": lunch_end_dt,
                }
            )

    # Check for dinner break (> 11 hours and spans dinner time)
    if current_hours > 11.0:
        if start_time < time(16, 0) and end_time > time(20, 0):
            # Get pseudorandom variation (0, 5, or 10 minutes)
            variation_minutes = get_pseudorandom_variation(session_id, "dinner") * 5
            # Use timedelta to handle minute overflow correctly
            base_dinner_start = datetime.combine(start_dt.date(), time(18, 10))
            dinner_start_dt = base_dinner_start + timedelta(minutes=variation_minutes)
            dinner_end_dt = dinner_start_dt + timedelta(minutes=45)
            dinner_start = dinner_start_dt.time()
            dinner_end = dinner_end_dt.time()

            breaks.append(
                {
                    "type": "dinner",
                    "start": dinner_start,
                    "end": dinner_end,
                    "start_dt": dinner_start_dt,
                    "end_dt": dinner_end_dt,
                }
            )

    return breaks


def split_session_at_breaks(event: Dict[str, Any], breaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Split a session into multiple sessions at break times.

    Args:
        event: Original event dictionary
        breaks: List of break dictionaries with start_dt and end_dt

    Returns:
        List of event dictionaries (split sessions)
    """
    if not breaks:
        return [event]

    start_dt = parse_datetime(event.get("start_datetime", ""))
    end_dt = parse_datetime(event.get("end_datetime", ""))

    if not start_dt or not end_dt:
        return [event]

    # Sort breaks by start time
    breaks_sorted = sorted(breaks, key=lambda b: b["start_dt"])

    # Create session segments
    sessions = []
    current_start = start_dt
    session_counter = 0

    for break_info in breaks_sorted:
        break_start = break_info["start_dt"]
        break_end = break_info["end_dt"]

        # Create session before break (if there's time)
        if current_start < break_start:
            session = event.copy()
            session["start_datetime"] = format_datetime(current_start)
            session["end_datetime"] = format_datetime(break_start)
            session_hours = calculate_hours(current_start, break_start)
            session["hours"] = f"{session_hours:.2f}"
            # Remove break info from description (clean it)
            original_desc = session.get("description", "")
            # Remove any existing break info in brackets
            if "[" in original_desc:
                original_desc = original_desc.split("[")[0].strip()
            session["description"] = original_desc
            # Update session_id to indicate split
            base_session_id = session.get("session_id", "").split(".")[0]
            session["session_id"] = f"{base_session_id}.{session_counter + 1}"
            sessions.append(session)
            session_counter += 1

        # Move to after break
        current_start = break_end

    # Create final session after last break (if there's time)
    if current_start < end_dt:
        session = event.copy()
        session["start_datetime"] = format_datetime(current_start)
        session["end_datetime"] = format_datetime(end_dt)
        session_hours = calculate_hours(current_start, end_dt)
        session["hours"] = f"{session_hours:.2f}"
        # Remove break info from description (clean it)
        original_desc = session.get("description", "")
        if "[" in original_desc:
            original_desc = original_desc.split("[")[0].strip()
        session["description"] = original_desc
        # Update session_id to indicate split
        base_session_id = session.get("session_id", "").split(".")[0]
        session["session_id"] = f"{base_session_id}.{session_counter + 1}"
        sessions.append(session)

    return sessions if sessions else [event]


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
    Process sessions to split at breaks and apply clipping rules.

    Args:
        events: List of calendar event dictionaries

    Returns:
        List of processed event dictionaries (may be more than input due to splitting)
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

            # Determine break times for long sessions
            breaks = determine_break_times(start_dt, end_dt, current_hours, session_id)

            # Split session at breaks
            split_sessions = split_session_at_breaks(event, breaks)

            # Process each split session
            for split_session in split_sessions:
                split_start_str = split_session.get("start_datetime", "")
                split_end_str = split_session.get("end_datetime", "")
                split_hours = float(split_session.get("hours", 0.0))

                if not split_start_str or not split_end_str:
                    continue

                split_start_dt = parse_datetime(split_start_str)
                split_end_dt = parse_datetime(split_end_str)
                split_date_str = split_start_dt.strftime("%Y-%m-%d")
                split_iso_week_str, split_iso_year, split_iso_week = get_iso_week(split_start_dt)

                # Check daily limit (10 hours/day)
                daily_total = daily_hours[split_date_str]
                if daily_total + split_hours > 10.0:
                    # Clip this session to fit within daily limit
                    remaining_daily_hours = 10.0 - daily_total
                    if remaining_daily_hours > 0:
                        # Adjust end time to fit remaining hours
                        max_duration = timedelta(hours=remaining_daily_hours)
                        split_end_dt = split_start_dt + max_duration
                        split_hours = remaining_daily_hours
                    else:
                        # Skip this session (day already at limit)
                        print(f"⚠️  Skipping {split_session.get('session_id', 'unknown')}: daily limit reached for {split_date_str}")
                        continue

                # Check weekly limit (40 hours/week)
                weekly_total = weekly_hours[split_iso_week_str]
                if weekly_total + split_hours > 40.0:
                    # Clip this session to fit within weekly limit
                    remaining_weekly_hours = 40.0 - weekly_total
                    if remaining_weekly_hours > 0:
                        # Adjust end time to fit remaining hours
                        max_duration = timedelta(hours=remaining_weekly_hours)
                        split_end_dt = split_start_dt + max_duration
                        split_hours = remaining_weekly_hours
                    else:
                        # Skip this session (week already at limit)
                        print(
                            f"⚠️  Skipping {split_session.get('session_id', 'unknown')}: weekly limit reached for {split_iso_week_str}"
                        )
                        continue

                # Clip to daily limit (safety check)
                split_start_dt, split_end_dt = clip_session_to_daily_limit(split_start_dt, split_end_dt, max_hours_per_day=10.0)
                split_hours = calculate_hours(split_start_dt, split_end_dt)

                # Update split session with processed data
                split_session["start_datetime"] = format_datetime(split_start_dt)
                split_session["end_datetime"] = format_datetime(split_end_dt)
                split_session["hours"] = f"{split_hours:.2f}"
                split_session["date"] = split_date_str
                split_session["iso_week_number"] = split_iso_week_str
                split_session["iso_year"] = str(split_iso_year)
                split_session["iso_week"] = str(split_iso_week)

                processed_events.append(split_session)

                # Update daily and weekly totals
                daily_hours[split_date_str] += split_hours
                weekly_hours[split_iso_week_str] += split_hours

            # Log long sessions that were split
            if current_hours > 6.0 and breaks:
                break_info = ", ".join([f"{b['type']} {b['start'].strftime('%H:%M')}-{b['end'].strftime('%H:%M')}" for b in breaks])
                print(
                    f"📝 Split long session {session_id}: {current_hours:.2f}h into {len(split_sessions)} sessions "
                    f"(breaks: {break_info})"
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
    print("Processing sessions (splitting at breaks, applying clipping rules)...")
    processed_events = process_sessions_with_breaks_and_clipping(events)
    print(f"Processed {len(processed_events)} events (from {len(events)} original)")
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
    print("Next steps:")
    print(f"1. Review fixed events in: {CALENDAR_EVENTS_FIXED}")
    print("2. If total hours > 750, replace original file and regenerate summaries")
    print("3. Run: python scripts/generate_weekly_summary.py")
    print()

    if new_total > 750.0:
        print(f"✅ Total hours ({new_total:.2f}) exceeds 750 - ready for commit and calendar update")
    else:
        print(f"⚠️  Total hours ({new_total:.2f}) is below 750 - review needed")


if __name__ == "__main__":
    main()
