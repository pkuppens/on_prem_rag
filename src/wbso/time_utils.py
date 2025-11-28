#!/usr/bin/env python3
"""
Time Utilities for WBSO Calendar Events

Provides time rounding and manipulation utilities for calendar events.

Author: AI Assistant
Created: 2025-11-28
"""

from datetime import datetime, timedelta
from typing import Optional

# Import shared datetime parsing with timezone support
from backend.datetime_utils import parse_datetime_with_timezone, AMSTERDAM_TZ

# Re-export for convenience
__all__ = [
    "round_to_quarter_hour",
    "add_deterministic_variation",
    "calculate_work_hours_with_breaks",
    "generate_lunch_break",
    "generate_dinner_break",
    "generate_work_break",
    "clip_to_max_daily_hours",
    "parse_datetime_flexible",
    "AMSTERDAM_TZ",
]


def parse_datetime_flexible(dt_str: str) -> Optional[datetime]:
    """
    Parse datetime string in various formats, returning timezone-aware datetime.

    Supports formats including:
    - Standard formats: YYYY-MM-DD HH:MM:SS, YYYY/MM/DD HH:MM:SS
    - ISO formats: YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SS+02:00
    - Timezone offsets: +0100, +0200 (without colon)
    - AM/PM formats: M/D/YYYY H:MM:SS AM/PM

    If timezone information is missing, assumes Amsterdam timezone (with DST).

    Args:
        dt_str: DateTime string in various formats

    Returns:
        Timezone-aware datetime object (Europe/Amsterdam) or None if parsing fails
    """
    return parse_datetime_with_timezone(dt_str, default_tz=AMSTERDAM_TZ)


def round_to_quarter_hour(dt: datetime) -> datetime:
    """
    Round datetime to nearest 5-minute interval (quarter hour preference).

    Rounding rules:
    - 0-3 minutes → 0
    - 4-7 minutes → 5
    - 8-11 minutes → 10
    - 12-18 minutes → 15
    - 19-23 minutes → 20
    - 24-28 minutes → 25
    - 29-33 minutes → 30
    - 34-38 minutes → 35
    - 39-43 minutes → 40
    - 44-48 minutes → 45
    - 49-53 minutes → 50
    - 54-56 minutes → 55
    - 57-59 minutes → 0 (next hour)

    Args:
        dt: Datetime to round

    Returns:
        Rounded datetime
    """
    minute = dt.minute
    hour = dt.hour

    # Determine rounded minute
    if minute <= 3:
        rounded_minute = 0
    elif minute <= 7:
        rounded_minute = 5
    elif minute <= 11:
        rounded_minute = 10
    elif minute <= 18:
        rounded_minute = 15
    elif minute <= 23:
        rounded_minute = 20
    elif minute <= 28:
        rounded_minute = 25
    elif minute <= 33:
        rounded_minute = 30
    elif minute <= 38:
        rounded_minute = 35
    elif minute <= 43:
        rounded_minute = 40
    elif minute <= 48:
        rounded_minute = 45
    elif minute <= 53:
        rounded_minute = 50
    elif minute <= 56:
        rounded_minute = 55
    else:  # 57-59 minutes
        rounded_minute = 0
        hour += 1
        # Handle hour overflow (next day)
        if hour >= 24:
            hour = 0

    # Create rounded datetime
    rounded = dt.replace(minute=rounded_minute, second=0, microsecond=0)
    if hour != dt.hour:
        rounded = rounded.replace(hour=hour)

    return rounded


def add_deterministic_variation(base_time: datetime, seed: str, max_minutes: int = 10) -> datetime:
    """
    Add deterministic time variation based on a seed.

    Uses the seed to generate a consistent offset for the same input time.
    This ensures the same commit timestamp always gets the same variation.

    Args:
        base_time: Base datetime to vary
        seed: Seed string (e.g., commit hash or session_id) for deterministic variation
        max_minutes: Maximum variation in minutes (default 10)

    Returns:
        Datetime with deterministic variation applied
    """
    # Generate deterministic offset from seed
    # Use simple hash of seed to get consistent offset
    seed_hash = hash(seed)
    offset_minutes = (seed_hash % (max_minutes * 2 + 1)) - max_minutes  # Range: -max_minutes to +max_minutes

    # Apply variation (20% chance of variation)
    variation_chance = abs(seed_hash) % 10
    if variation_chance < 2:  # 20% chance
        return base_time + timedelta(minutes=offset_minutes)
    else:
        return base_time


def calculate_work_hours_with_breaks(start_time: datetime, end_time: datetime, breaks: list[dict]) -> float:
    """
    Calculate work hours excluding breaks.

    Args:
        start_time: Session start time
        end_time: Session end time
        breaks: List of break dictionaries with 'start' and 'end' datetime keys

    Returns:
        Work hours (excluding breaks)
    """
    total_duration = (end_time - start_time).total_seconds() / 3600.0

    # Subtract break durations
    break_duration = 0.0
    for break_period in breaks:
        break_start = break_period["start"]
        break_end = break_period["end"]
        break_duration += (break_end - break_start).total_seconds() / 3600.0

    return total_duration - break_duration


def generate_lunch_break(date: datetime, seed: str) -> dict:
    """
    Generate lunch break time (12:00, 12:15, or 12:30 start, 25-40 minutes duration).

    Args:
        date: Date for the break
        seed: Seed for deterministic variation

    Returns:
        Dictionary with 'start' and 'end' datetime keys
    """
    seed_hash = hash(seed)

    # Start time: 12:00, 12:15, or 12:30
    start_minutes = [0, 15, 30][abs(seed_hash) % 3]

    # Duration: 25, 30, or 40 minutes
    durations = [25, 30, 40]
    duration_minutes = durations[abs(seed_hash) % 3]

    start_time = date.replace(hour=12, minute=start_minutes, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=duration_minutes)

    return {"start": start_time, "end": end_time, "type": "lunch", "duration_minutes": duration_minutes}


def generate_dinner_break(date: datetime, seed: str) -> dict:
    """
    Generate dinner break time (random 5-minute timestamp between 17:30 and 18:15, 30-50 minutes duration).

    Args:
        date: Date for the break
        seed: Seed for deterministic variation

    Returns:
        Dictionary with 'start' and 'end' datetime keys
    """
    seed_hash = hash(seed)

    # Start time: random 5-minute interval between 17:30 and 18:15
    # 17:30, 17:35, 17:40, 17:45, 17:50, 17:55, 18:00, 18:05, 18:10, 18:15
    start_minutes_options = [30, 35, 40, 45, 50, 55, 0, 5, 10, 15]
    start_minute = start_minutes_options[abs(seed_hash) % len(start_minutes_options)]
    start_hour = 17 if start_minute >= 30 else 18

    # Duration: 30-50 minutes (in 5-minute increments)
    duration_options = [30, 35, 40, 45, 50]
    duration_minutes = duration_options[abs(seed_hash) % len(duration_options)]

    start_time = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=duration_minutes)

    return {"start": start_time, "end": end_time, "type": "dinner", "duration_minutes": duration_minutes}


def generate_work_break(start_time: datetime, end_time: datetime, seed: str) -> Optional[dict]:
    """
    Generate a 20-50 minutes break for work blocks longer than 6 hours.

    Args:
        start_time: Session start time
        end_time: Session end time
        seed: Seed for deterministic variation

    Returns:
        Dictionary with 'start' and 'end' datetime keys, or None if not needed
    """
    duration_hours = (end_time - start_time).total_seconds() / 3600.0

    # Only add break if duration > 6 hours
    if duration_hours <= 6.0:
        return None

    seed_hash = hash(seed)

    # Place break at approximately 55-60% of the work duration, before rounding to 5-minute interval
    percent = 0.55 + (abs(seed_hash) % 6) * 0.01  # 55% to 60% (increments of 1%)
    break_offset = (end_time - start_time) * percent
    mid_point = start_time + break_offset

    # Round to nearest 5 minutes
    rounded_minute = (mid_point.minute // 5) * 5
    break_start = mid_point.replace(minute=rounded_minute, second=0, microsecond=0)

    # Add small variation based on seed; must be a multiple of 5 between -10 and +10, weighted toward 0
    variation_options = [-10, -5, -5, 0, 0, 0, 0, 5, 5, 10]
    variation = variation_options[abs(seed_hash) % len(variation_options)]
    break_start = break_start + timedelta(minutes=variation)

    # Add variability to the break length based on a new seed
    base_break_minutes = 30
    break_seed_hash = hash(seed + "break")
    break_length_options = [v + base_break_minutes for v in variation_options]
    break_duration_minutes = break_length_options[abs(break_seed_hash) % len(break_length_options)]

    # Add 10 minutes if break start after 17:00
    if break_start.hour >= 17:
        break_duration_minutes += 10

    # Ensure break doesn't go before start or after end
    if break_start < start_time:
        break_start = start_time
    if break_start > end_time - timedelta(minutes=break_duration_minutes):
        break_start = end_time - timedelta(minutes=break_duration_minutes)

    break_end = break_start + timedelta(minutes=break_duration_minutes)

    return {"start": break_start, "end": break_end, "type": "work_break", "duration_minutes": break_duration_minutes}


def clip_to_max_daily_hours(start_time: datetime, end_time: datetime, max_hours: float = 11.0) -> datetime:
    """
    Clip end time to ensure total work hours don't exceed max_hours per day.

    Args:
        start_time: Session start time
        end_time: Session end time
        max_hours: Maximum hours allowed per day (default 11.0)

    Returns:
        Clipped end time
    """
    duration_hours = (end_time - start_time).total_seconds() / 3600.0

    if duration_hours <= max_hours:
        return end_time

    # Clip to max_hours
    clipped_end = start_time + timedelta(hours=max_hours)

    # Round to nearest 5 minutes
    rounded_minute = (clipped_end.minute // 5) * 5
    if rounded_minute == 60:
        rounded_minute = 55

    clipped_end = clipped_end.replace(minute=rounded_minute, second=0, microsecond=0)

    return clipped_end
