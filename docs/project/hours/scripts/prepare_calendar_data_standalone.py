#!/usr/bin/env python3
"""
Standalone Google Calendar Data Preparation Script

This script allows running the Google Calendar data preparation step independently
without executing the full pipeline or uploading to Google Calendar.

Usage:
    python prepare_calendar_data_standalone.py [input_file] [output_file]

If input_file is not provided, it will attempt to load from the pipeline context.
If output_file is not provided, it will save to upload_output/prepared_calendar_events.json

Author: AI Assistant
Created: 2025-11-29
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.wbso.calendar_event import CalendarEvent, WBSODataset
from src.wbso.logging_config import get_logger
from src.wbso.pipeline_steps import step_google_calendar_data_preparation

logger = get_logger("prepare_calendar_data_standalone")

# Default paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
VALIDATION_OUTPUT_DIR = SCRIPT_DIR.parent / "validation_output"
UPLOAD_OUTPUT_DIR = SCRIPT_DIR.parent / "upload_output"


def load_calendar_events_from_file(file_path: Path) -> List[CalendarEvent]:
    """Load calendar events from JSON file."""
    logger.info(f"Loading calendar events from {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = []

    # Handle different JSON structures
    if isinstance(data, dict):
        if "calendar_events" in data:
            events_data = data["calendar_events"]
        elif "events" in data:
            events_data = data["events"]
        else:
            # Assume the dict itself is an event
            events_data = [data]
    elif isinstance(data, list):
        events_data = data
    else:
        raise ValueError("Invalid JSON structure")

    # Convert to CalendarEvent objects
    for event_data in events_data:
        try:
            # Handle both dict and CalendarEvent-like structures
            if isinstance(event_data, dict):
                event = CalendarEvent(
                    summary=event_data.get("summary", ""),
                    description=event_data.get("description", ""),
                    start=event_data.get("start", {}),
                    end=event_data.get("end", {}),
                    color_id=event_data.get("color_id", "1"),
                    extended_properties=event_data.get("extended_properties", {}),
                    location=event_data.get("location", "Home Office"),
                    transparency=event_data.get("transparency", "opaque"),
                )
                events.append(event)
            else:
                logger.warning(f"Skipping invalid event data: {type(event_data)}")
        except Exception as e:
            logger.error(f"Failed to load event: {e}")

    logger.info(f"Loaded {len(events)} calendar events")
    return events


def load_calendar_events_from_pipeline_context() -> List[CalendarEvent]:
    """Attempt to load calendar events from pipeline context files."""
    logger.info("Attempting to load calendar events from pipeline context...")

    # Try to load from validation output (if event_convert step was run)
    possible_sources = [
        UPLOAD_OUTPUT_DIR / "pipeline_report.json",
        VALIDATION_OUTPUT_DIR / "cleaned_dataset.json",
    ]

    for source_path in possible_sources:
        if source_path.exists():
            try:
                with open(source_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Try to extract calendar events from pipeline report
                if isinstance(data, dict) and "steps" in data:
                    for step in data["steps"]:
                        if step.get("step_name") == "event_convert":
                            # Events might be in context, but we can't access them directly
                            # So we'll need to convert from sessions
                            logger.info("Found event_convert step in pipeline report")
                            break

                # Try to load from dataset and convert
                if "sessions" in data or "work_sessions" in data:
                    logger.info("Found sessions in data, attempting to convert...")
                    dataset = WBSODataset()
                    dataset.load_from_json(source_path)

                    # Convert sessions to events
                    from src.wbso.activities import WBSOActivities

                    activities_manager = WBSOActivities()
                    activities_manager.load_activities(force_regenerate=False)

                    events = []
                    for session in dataset.sessions:
                        if session.is_wbso:
                            try:
                                activity_name_nl = None
                                if session.activity_id:
                                    activity_name_nl = activities_manager.get_activity_name_nl(session.activity_id)
                                event = CalendarEvent.from_wbso_session(session, activity_name_nl=activity_name_nl)
                                events.append(event)
                            except Exception as e:
                                logger.warning(f"Failed to convert session {session.session_id}: {e}")

                    if events:
                        logger.info(f"Converted {len(events)} sessions to calendar events")
                        return events
            except Exception as e:
                logger.warning(f"Failed to load from {source_path}: {e}")
                continue

    raise FileNotFoundError("Could not find calendar events. Please provide input file or run event_convert step first.")


def save_prepared_events(events: List[CalendarEvent], output_path: Path) -> None:
    """Save prepared calendar events to JSON file."""
    logger.info(f"Saving {len(events)} prepared events to {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert events to dict format
    events_data = []
    for event in events:
        event_dict = {
            "summary": event.summary,
            "description": event.description,
            "start": event.start,
            "end": event.end,
            "color_id": event.color_id,
            "extended_properties": event.extended_properties,
            "location": event.location,
            "transparency": event.transparency,
        }
        events_data.append(event_dict)

    output_data = {
        "prepared_timestamp": datetime.now().isoformat(),
        "event_count": len(events_data),
        "calendar_events": events_data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Saved prepared events to {output_path}")


def main() -> int:
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("GOOGLE CALENDAR DATA PREPARATION (STANDALONE)")
    logger.info("=" * 60)

    # Parse arguments
    input_file = None
    output_file = None

    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = UPLOAD_OUTPUT_DIR / "prepared_calendar_events.json"

    try:
        # Load calendar events
        if input_file:
            calendar_events = load_calendar_events_from_file(input_file)
        else:
            calendar_events = load_calendar_events_from_pipeline_context()

        if not calendar_events:
            logger.error("No calendar events to prepare")
            return 1

        # Create context
        context = {
            "calendar_events": calendar_events,
            "dry_run": True,  # No actual upload
        }

        # Run preparation step
        logger.info("Running preparation step...")
        report = step_google_calendar_data_preparation(context)

        # Get prepared events
        prepared_events = context.get("calendar_events", [])

        # Save prepared events
        save_prepared_events(prepared_events, output_file)

        # Print summary
        print(f"\n{'=' * 60}")
        print("PREPARATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Input Events: {report.get('input_count', 0)}")
        print(f"Output Events: {report.get('output_count', 0)}")
        print(f"Filtered Out: {report.get('filtered_count', 0)}")
        print(f"Corrections Applied: {report.get('corrections_count', 0)}")
        print(f"Total Hours Before: {report.get('total_hours_before', 0):.2f}")
        print(f"Total Hours After: {report.get('total_hours_after', 0):.2f}")
        print(f"Hours That Could Be Added: {report.get('hours_that_could_be_added', 0):.2f}")
        print(f"\nOutput saved to: {output_file}")
        print(f"{'=' * 60}\n")

        # Save report
        report_path = UPLOAD_OUTPUT_DIR / "preparation_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to {report_path}")

        return 0 if report.get("success", False) else 1

    except Exception as e:
        logger.error(f"Preparation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
