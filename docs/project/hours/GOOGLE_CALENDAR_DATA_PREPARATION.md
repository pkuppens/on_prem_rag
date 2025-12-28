# Google Calendar Data Preparation

**Document Version**: 1.0  
**Created**: 2025-11-29  
**Last Updated**: 2025-11-29

## Overview

This document describes the Google Calendar data preparation step in the WBSO pipeline. This step prepares calendar events for upload to Google Calendar by applying corrections, filters, and adding metadata like ISO week numbers.

## Project Context

The WBSO (Wet Bevordering Speur- en Ontwikkelingswerk) hours registration system tracks research and development work hours for tax deduction purposes. Calendar events are created from work sessions and uploaded to Google Calendar for tracking and compliance reporting.

### WBSO Project

- **Project ID**: WBSO-AICM-2025-01
- **Project Name**: AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving
- **Target Hours**: 510 hours per year
- **Date Range**: 2025-06-01 to present

## Data Processing

### Input Data

The preparation step receives calendar events from the `step_event_convert` step. Each event is a `CalendarEvent` object with the following structure:

```python
CalendarEvent(
    summary: str,              # Event title (e.g., "AI Framework Ontwikkeling")
    description: str,          # Detailed description in Dutch
    start: Dict[str, str],      # {"dateTime": "2025-01-15T09:00:00", "timeZone": "Europe/Amsterdam"}
    end: Dict[str, str],        # {"dateTime": "2025-01-15T17:00:00", "timeZone": "Europe/Amsterdam"}
    color_id: str,             # Calendar color (default: "1" for blue)
    extended_properties: Dict, # WBSO metadata (private properties)
    location: str,             # "Thuiswerk" or "Kantoor"
    transparency: str          # "opaque" (default)
)
```

### Extended Properties

Each event includes WBSO metadata in `extended_properties.private`:

- `wbso_project`: "WBSO-AICM-2025-01"
- `wbso_category`: One of AI_FRAMEWORK, ACCESS_CONTROL, PRIVACY_CLOUD, AUDIT_LOGGING, DATA_INTEGRITY, GENERAL_RD
- `session_id`: Unique session identifier
- `work_hours`: Work hours as string (e.g., "8.0")
- `is_synthetic`: Whether session is synthetic (generated from commits)
- `commit_count`: Number of commits in session
- `source_type`: "real" or "synthetic"
- `confidence_score`: Confidence score (0.0 to 1.0)
- `activity_id`: WBSO activity ID (optional)

### Output Data

After preparation, events include additional metadata:

- `iso_week_number`: ISO week number in format "YYYY-WNN" (e.g., "2025-W03")
- `iso_year`: ISO year (e.g., "2025")
- `iso_week`: ISO week number (1-53, e.g., "3")
- `iso_weekday`: ISO weekday (1=Monday, 7=Sunday, e.g., "1")

## Google Calendar API Requirements

### Current API Version

The system uses **Google Calendar API v3** with the following requirements:

### Event Format

Events must conform to the Google Calendar API event resource format:

```json
{
  "summary": "Event Title",
  "description": "Event description",
  "start": {
    "dateTime": "2025-01-15T09:00:00",
    "timeZone": "Europe/Amsterdam"
  },
  "end": {
    "dateTime": "2025-01-15T17:00:00",
    "timeZone": "Europe/Amsterdam"
  },
  "colorId": "1",
  "extendedProperties": {
    "private": {
      "wbso_project": "WBSO-AICM-2025-01",
      "wbso_category": "AI_FRAMEWORK",
      "session_id": "session_123",
      "work_hours": "8.0",
      "iso_week_number": "2025-W03"
    }
  },
  "location": "Thuiswerk",
  "transparency": "opaque"
}
```

### API Constraints

1. **DateTime Format**: Must be in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`
2. **TimeZone**: Must be specified (we use "Europe/Amsterdam")
3. **Duration**: Events must have positive duration (end > start)
4. **Extended Properties**: Private properties are limited to 150 bytes per property value
5. **Summary Length**: Maximum 1024 characters
6. **Description Length**: Maximum 8192 characters

### Validation Rules

The Google Calendar API enforces:

- `start.dateTime` must be before `end.dateTime`
- Both `start` and `end` must have `dateTime` and `timeZone` fields
- `dateTime` must be valid ISO 8601 format
- `timeZone` must be a valid IANA timezone identifier

## Preparation Steps

### 1. Time Corrections

The preparation step applies corrections to fix common time issues:

#### Correction: Midnight End Time

**Problem**: Events ending at midnight (00:00:00) on the same day as start time.

**Example**: `18:00:00 - 00:00:00` (same day)

**Correction**: Set end time to `23:59:59` of the start day.

**Rationale**: Google Calendar requires end time to be after start time. Midnight on the same day is invalid.

#### Correction: End Before Start

**Problem**: End time is before start time (data error).

**Correction**: Set end time to `23:59:59` of the start day.

**Rationale**: Ensures valid event duration.

### 2. Filtering

The preparation step filters out invalid events:

#### Filter: Zero or Negative Duration

**Removes**: Events where `end <= start`

**Reason**: Invalid event duration

#### Filter: Duration Exceeds 24 Hours

**Removes**: Events longer than 24 hours

**Reason**: Likely data errors (work sessions should not exceed 24 hours)

### 3. Metadata Addition

The preparation step adds ISO week number metadata:

- Calculates ISO week number from event start date
- Adds to `extended_properties.private`:
  - `iso_week_number`: "YYYY-WNN" format
  - `iso_year`: ISO year
  - `iso_week`: ISO week (1-53)
  - `iso_weekday`: ISO weekday (1-7)

**ISO Week Calculation**: Uses Python's `datetime.isocalendar()` which follows ISO 8601 standard:

- Week starts on Monday (weekday 1)
- Week 1 is the first week with a Thursday
- Year can have 52 or 53 weeks

## Error Handling

The preparation step includes comprehensive error handling:

1. **Parse Errors**: If datetime parsing fails, event is filtered out with error logged
2. **Corrections**: Corrected events are stored, with the correction and reason logged as info
3. **Validation Errors**: Invalid events are filtered out with reason logged as warning
4. **Metadata Errors**: If ISO week calculation fails, event is still processed (metadata may be missing)

All errors are logged and included in the step report.

## Reporting

The preparation step generates a comprehensive report including:

- **Input Statistics**: Number of input events, total hours
- **Output Statistics**: Number of output events, total hours
- **Corrections Applied**: List of corrections with details
- **Filtered Events**: List of filtered events with reasons
- **Hours Summary**: Hours before/after processing, hours that could be added

## Standalone Execution

The preparation step can run standalone on input data without actual upload:

```python
from src.wbso.pipeline_steps import step_google_calendar_data_preparation
from src.wbso.calendar_event import CalendarEvent

# Load calendar events from file or create test events
calendar_events = [...]  # List of CalendarEvent objects

# Create context
context = {
    "calendar_events": calendar_events,
    "dry_run": True,  # No actual upload
}

# Run preparation step
report = step_google_calendar_data_preparation(context)

# Access prepared events
prepared_events = context["calendar_events"]

# Access report
print(f"Input: {report['input_count']} events")
print(f"Output: {report['output_count']} events")
print(f"Hours: {report['hours_that_could_be_added']:.2f}")
```

## Integration

The preparation step is integrated into the WBSO pipeline between:

1. **step_event_convert**: Converts WBSO sessions to calendar events
2. **step_google_calendar_data_preparation**: Prepares events (this step)
3. **step_calendar_replace**: Uploads events to Google Calendar

## Code Files

- [src/wbso/pipeline_steps.py](src/wbso/pipeline_steps.py) - Pipeline step implementation
- [src/wbso/calendar_event.py](src/wbso/calendar_event.py) - CalendarEvent data model
- [src/wbso/pipeline.py](src/wbso/pipeline.py) - Pipeline orchestration
- [docs/project/hours/scripts/prepare_calendar_data_standalone.py](docs/project/hours/scripts/prepare_calendar_data_standalone.py) - Standalone execution script

## References

- [Google Calendar API v3 Documentation](https://developers.google.com/calendar/api/v3/reference/events)
- [ISO 8601 Week Date Standard](https://en.wikipedia.org/wiki/ISO_8601#Week_dates)
- [WBSO-DATA-FLOW.md](WBSO-DATA-FLOW.md) - Complete WBSO data flow documentation
