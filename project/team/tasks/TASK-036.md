# TASK-036: Google Calendar Population with Conflict Resolution

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Implement Google Calendar population with intelligent conflict detection and resolution. The system should detect conflicts between WBSO work sessions and existing calendar events, and handle them according to predefined rules for short vs long conflicts.

## Business Context

When populating the WBSO Google Calendar, conflicts with existing personal appointments may occur. The system needs to intelligently handle these conflicts:

- Short conflicts (<2 hours): Automatically adjust WBSO session times
- Long conflicts (≥2 hours): Flag for review (may be holiday work scenarios)

## Acceptance Criteria

- [x] **Conflict Detection**: Detect overlaps between WBSO events and existing calendar events
- [x] **Conflict Classification**: Classify conflicts as short (<2 hours) or long (≥2 hours)
- [x] **Short Conflict Handling**: Automatically adjust WBSO session times for short conflicts
- [x] **Long Conflict Handling**: Flag long conflicts for manual review
- [x] **Conflict Reporting**: Generate detailed conflict reports for review
- [x] **Event Processing**: Process all WBSO events with conflict information
- [x] **Calendar Compatibility**: Ensure processed events are ready for Google Calendar API

## Technical Requirements

### Conflict Detection Algorithm

```python
def detect_conflicts(wbso_event, existing_events):
    """Detect conflicts between WBSO event and existing calendar events."""
    conflicts = []
    wbso_start = parse_datetime(wbso_event['start']['dateTime'])
    wbso_end = parse_datetime(wbso_event['end']['dateTime'])

    for existing_event in existing_events:
        existing_start = parse_datetime(existing_event['start']['dateTime'])
        existing_end = parse_datetime(existing_event['end']['dateTime'])

        overlap_hours = calculate_overlap(wbso_start, wbso_end, existing_start, existing_end)

        if overlap_hours > 0:
            conflict = {
                'existing_event': existing_event,
                'overlap_hours': overlap_hours,
                'conflict_type': 'short' if overlap_hours < 2.0 else 'long'
            }
            conflicts.append(conflict)

    return conflicts
```

### Conflict Resolution Rules

1. **Short Conflicts (<2 hours)**

   - Automatically adjust WBSO session times
   - Add conflict information to event metadata
   - Flag for review but allow population

2. **Long Conflicts (≥2 hours)**
   - Flag for manual review
   - Include conflict details in event metadata
   - Allow population (may be holiday work scenarios)

### Event Processing Output

```json
{
  "processed_events": [
    {
      "summary": "WBSO: AI Framework Development",
      "start": {
        "dateTime": "2025-05-05T13:00:00",
        "timeZone": "Europe/Amsterdam"
      },
      "end": {
        "dateTime": "2025-05-05T17:00:00",
        "timeZone": "Europe/Amsterdam"
      },
      "extendedProperties": {
        "private": {
          "has_conflicts": "true",
          "conflict_count": "1",
          "conflicts": "[{\"overlap_hours\": 1.5, \"conflict_type\": \"short\", \"existing_event_summary\": \"Doctor Appointment\"}]"
        }
      }
    }
  ],
  "summary": {
    "total_events": 94,
    "events_with_conflicts": 0,
    "events_without_conflicts": 94,
    "conflict_percentage": 0.0
  }
}
```

### Conflict Report Format

```json
{
  "conflict_reports": [
    {
      "wbso_event_summary": "WBSO: AI Framework Development",
      "wbso_event_start": "2025-05-05T13:00:00",
      "wbso_event_end": "2025-05-05T17:00:00",
      "conflict_count": 1,
      "conflicts": [
        {
          "existing_event_summary": "Doctor Appointment",
          "existing_event_start": "2025-05-05T14:00:00",
          "existing_event_end": "2025-05-05T15:30:00",
          "overlap_hours": 1.5,
          "conflict_type": "short"
        }
      ]
    }
  ]
}
```

## Implementation Steps

1. **Conflict Detection**

   - Parse WBSO event and existing event timestamps
   - Calculate overlap duration between events
   - Classify conflicts as short or long

2. **Conflict Processing**

   - Apply conflict resolution rules
   - Add conflict information to event metadata
   - Generate conflict reports

3. **Event Adjustment**

   - For short conflicts: adjust WBSO session times
   - For long conflicts: flag for review
   - Maintain event integrity and metadata

4. **Output Generation**

   - Create processed events with conflict information
   - Generate comprehensive conflict reports
   - Ensure Google Calendar API compatibility

5. **Validation and Testing**
   - Test conflict detection accuracy
   - Validate event processing logic
   - Ensure proper metadata handling

## Dependencies

- `docs/project/hours/data/wbso_calendar_events.json` - WBSO calendar events
- `docs/project/hours/data/calendar_events_2025.csv` - Existing calendar events
- Google Calendar API compatibility requirements

## Definition of Done

- [x] Conflict detection algorithm implemented and tested
- [x] 94 WBSO events processed for conflicts
- [x] 0 conflicts detected (no existing calendar events overlap)
- [x] Conflict resolution logic implemented
- [x] Processed events ready for Google Calendar API
- [x] Comprehensive conflict reporting system
- [x] Event metadata includes conflict information
- [x] Code reviewed and committed to repository

## Results Summary

### Conflict Detection Results

- **Total WBSO Events Processed**: 94 events
- **Events with Conflicts**: 0 events
- **Events without Conflicts**: 94 events
- **Conflict Percentage**: 0.0%

### Processing Statistics

- **Total Events**: 94 processed events
- **Real Events**: 37 events (from system events)
- **Synthetic Events**: 57 events (from unassigned commits)
- **Total Hours**: 438.27 WBSO hours

### Conflict Resolution Features

- **Automatic Detection**: Overlap calculation between WBSO and existing events
- **Conflict Classification**: Short (<2 hours) vs long (≥2 hours) conflicts
- **Event Adjustment**: Automatic time adjustment for short conflicts
- **Review Flagging**: Manual review flagging for long conflicts
- **Metadata Integration**: Conflict information included in event metadata

### Calendar Compatibility

- **Google Calendar API**: Full compatibility with event format
- **Timezone Handling**: Proper Europe/Amsterdam timezone support
- **Event Properties**: Extended properties for WBSO metadata
- **Conflict Information**: Detailed conflict data in event metadata

## Estimated Effort

- **Script Development**: 3 hours
- **Conflict Detection Logic**: 2 hours
- **Testing and Validation**: 1 hour
- **Documentation**: 1 hour
- **Total**: 7 hours

## Related Files

- [docs/project/hours/scripts/populate_wbso_calendar.py](docs/project/hours/scripts/populate_wbso_calendar.py) - Main calendar population script
- [docs/project/hours/data/wbso_calendar_events_processed.json](docs/project/hours/data/wbso_calendar_events_processed.json) - Processed events with conflict information
- [docs/project/hours/data/calendar_conflict_reports.json](docs/project/hours/data/calendar_conflict_reports.json) - Conflict reports
- [project/team/tasks/TASK-035.md](project/team/tasks/TASK-035.md) - WBSO justification generator (prerequisite)

## Code Files

- [docs/project/hours/scripts/populate_wbso_calendar.py](docs/project/hours/scripts/populate_wbso_calendar.py) - Calendar population with conflict detection and resolution
- [docs/project/hours/data/wbso_calendar_events_processed.json](docs/project/hours/data/wbso_calendar_events_processed.json) - Processed events ready for Google Calendar
- [docs/project/hours/data/calendar_conflict_reports.json](docs/project/hours/data/calendar_conflict_reports.json) - Detailed conflict reports

## Notes

This task successfully implemented conflict detection and resolution for WBSO calendar events. The system processed 94 events and found no conflicts with existing calendar events, indicating that the WBSO work sessions don't overlap with personal appointments.

The conflict resolution system is ready to handle future conflicts according to the specified rules:

- Short conflicts (<2 hours) will be automatically adjusted
- Long conflicts (≥2 hours) will be flagged for manual review

All processed events are ready for Google Calendar API integration and include comprehensive metadata for WBSO compliance and conflict tracking.
