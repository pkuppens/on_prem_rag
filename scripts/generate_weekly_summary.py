#!/usr/bin/env python3
"""
Generate weekly summary report of hours by description and ISO week.

Reads calendar events CSV and creates a summary grouped by ISO week number
and description (activity name).

Author: AI Assistant
Created: 2025-12-02
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Paths
SCRIPT_DIR = Path(__file__).parent.parent / "docs" / "project" / "hours"
DATA_DIR = SCRIPT_DIR / "data"
CALENDAR_EVENTS_CSV = DATA_DIR / "calendar_events.csv"
OUTPUT_MD = SCRIPT_DIR / "SUMMARY_BY_WEEK.md"


def load_calendar_events() -> List[Dict[str, str]]:
    """Load calendar events from CSV."""
    if not CALENDAR_EVENTS_CSV.exists():
        raise FileNotFoundError(f"Calendar events CSV not found: {CALENDAR_EVENTS_CSV}")

    events = []
    with open(CALENDAR_EVENTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)

    return events


def generate_summary(events: List[Dict[str, str]]) -> Dict[str, Dict[str, float]]:
    """Generate summary grouped by ISO week and description.

    Returns:
        Dict[iso_week_number, Dict[description, total_hours]]
    """
    summary: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for event in events:
        iso_week = event.get("iso_week_number", "").strip()
        description = event.get("description", "").strip()
        hours_str = event.get("hours", "0").strip()

        if not iso_week or not description:
            continue

        try:
            hours = float(hours_str)
            summary[iso_week][description] += hours
        except (ValueError, TypeError):
            continue

    return dict(summary)


def format_markdown_report(summary: Dict[str, Dict[str, float]]) -> str:
    """Format summary as markdown report."""
    lines = []

    # Header
    lines.append("# WBSO Hours Summary by ISO Week")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("This report summarizes hours spent on each activity (description) grouped by ISO week number.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sort weeks chronologically
    sorted_weeks = sorted(summary.keys(), key=lambda w: (int(w.split("-")[0]), int(w.split("-W")[1])))

    # Overall statistics
    total_hours_all = sum(sum(desc_hours.values()) for desc_hours in summary.values())
    total_weeks = len(sorted_weeks)
    all_descriptions = set()
    for week_data in summary.values():
        all_descriptions.update(week_data.keys())
    total_activities = len(all_descriptions)

    lines.append("## Summary Statistics")
    lines.append("")
    lines.append(f"- **Total Hours**: {total_hours_all:.2f}")
    lines.append(f"- **Total Weeks**: {total_weeks}")
    lines.append(f"- **Total Activities**: {total_activities}")
    lines.append(f"- **Date Range**: {sorted_weeks[0] if sorted_weeks else 'N/A'} to {sorted_weeks[-1] if sorted_weeks else 'N/A'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Weekly breakdown
    lines.append("## Weekly Breakdown")
    lines.append("")

    for week in sorted_weeks:
        week_data = summary[week]
        week_total = sum(week_data.values())

        lines.append(f"### {week}")
        lines.append("")
        lines.append(f"**Total Hours**: {week_total:.2f}")
        lines.append("")
        lines.append("| Activity | Hours |")
        lines.append("|----------|-------|")

        # Sort activities by hours (descending)
        sorted_activities = sorted(week_data.items(), key=lambda x: x[1], reverse=True)

        for description, hours in sorted_activities:
            # Escape pipe characters in description for markdown table
            description_escaped = description.replace("|", "\\|")
            lines.append(f"| {description_escaped} | {hours:.2f} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Activity totals across all weeks
    lines.append("## Activity Totals (All Weeks)")
    lines.append("")
    lines.append("| Activity | Total Hours | Weeks Active |")
    lines.append("|----------|-------------|--------------|")

    activity_totals: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0.0, 0))

    for week_data in summary.values():
        for description, hours in week_data.items():
            current_total, current_weeks = activity_totals[description]
            activity_totals[description] = (current_total + hours, current_weeks + 1)

    # Sort by total hours (descending)
    sorted_activities = sorted(activity_totals.items(), key=lambda x: x[1][0], reverse=True)

    for description, (total_hours, weeks_active) in sorted_activities:
        description_escaped = description.replace("|", "\\|")
        lines.append(f"| {description_escaped} | {total_hours:.2f} | {weeks_active} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Week totals
    lines.append("## Week Totals")
    lines.append("")
    lines.append("| Week | Total Hours | Activities |")
    lines.append("|------|-------------|-----------|")

    for week in sorted_weeks:
        week_data = summary[week]
        week_total = sum(week_data.values())
        activity_count = len(week_data)
        lines.append(f"| {week} | {week_total:.2f} | {activity_count} |")

    lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    print("Loading calendar events...")
    events = load_calendar_events()
    print(f"Loaded {len(events)} calendar events")

    print("Generating summary...")
    summary = generate_summary(events)
    print(f"Found {len(summary)} weeks with activity data")

    print("Formatting markdown report...")
    markdown = format_markdown_report(summary)

    print(f"Writing report to {OUTPUT_MD}...")
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"✅ Report generated successfully: {OUTPUT_MD}")

    # Print summary statistics
    total_hours = sum(sum(desc_hours.values()) for desc_hours in summary.values())
    print("\nSummary:")
    print(f"  - Total hours: {total_hours:.2f}")
    print(f"  - Total weeks: {len(summary)}")
    print(f"  - Total activities: {len(set(desc for week_data in summary.values() for desc in week_data.keys()))}")


if __name__ == "__main__":
    main()
