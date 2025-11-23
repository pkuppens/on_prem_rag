# MCP Calendar Server Requirements

This document specifies the functional and non-functional requirements for the MCP Calendar Server, which provides Google Calendar integration for WBSO hours registration.

**Author**: AI Assistant  
**Created**: 2025-11-16  
**Updated**: 2025-11-16

## Overview

The MCP Calendar Server exposes Google Calendar functionality through the Model Context Protocol (MCP). It provides tools for reading, creating, editing, and deleting calendar events, with security constraints to ensure write operations only target the WBSO calendar.

See [src/mcp/calendar_server.py](src/mcp/calendar_server.py) for the implementation.

## Non-Functional Requirements

### Security Requirements

**REQ-SEC-001**: The server shall only allow write operations (create, update, delete) to the "WBSO Activities 2025" calendar, regardless of OAuth scope permissions.

**REQ-SEC-002**: All write operations shall validate the target calendar ID against the allowed WBSO calendar ID before execution.

**REQ-SEC-003**: Write operations to read-only calendars shall be blocked with appropriate error messages.

**REQ-SEC-004**: Security violations (attempted writes to non-WBSO calendars) shall be logged as errors.

**REQ-SEC-005**: Read operations may access all accessible calendars for duplicate detection and conflict analysis.

### Error Handling Requirements

**REQ-ERR-001**: All tool calls shall handle errors gracefully and return structured error responses.

**REQ-ERR-002**: Invalid input parameters shall be validated and rejected with descriptive error messages.

**REQ-ERR-003**: HTTP errors from Google Calendar API shall be caught, logged, and returned in a structured format.

**REQ-ERR-004**: Date/time parsing errors shall be caught and returned with clear error messages.

### Logging Requirements

**REQ-LOG-001**: All tool operations shall log start and completion with appropriate log levels.

**REQ-LOG-002**: Event creation and upload operations shall log detailed event information (summary, dates, location, target calendar).

**REQ-LOG-003**: Security violations and permission errors shall be logged as errors.

**REQ-LOG-004**: API calls to Google Calendar shall be logged at debug level with relevant parameters.

### Data Format Requirements

**REQ-DATA-001**: All date/time values shall be handled in Amsterdam timezone (Europe/Amsterdam) with automatic DST handling.

**REQ-DATA-002**: Date/time values sent to Google Calendar API shall be converted to UTC and formatted as RFC3339 (YYYY-MM-DDTHH:MM:SSZ).

**REQ-DATA-003**: Date/time values in ISO format shall support both timezone-aware and timezone-naive formats.

## Functional Requirements by Tool

### Tool 1: list_calendars

**REQ-LIST-001**: The server shall provide a tool named `list_calendars` that returns all accessible Google Calendars.

**REQ-LIST-002**: The tool shall return calendars sorted alphabetically by summary (name).

**REQ-LIST-003**: For each calendar, the tool shall return:

- Calendar ID
- Summary (name)
- Access role (owner, writer, reader, freeBusyReader)
- Description (if available)
- Timezone (if available)

**REQ-LIST-004**: The tool shall require no input parameters.

**REQ-LIST-005**: The tool shall return a JSON object with:

- `calendars`: Array of calendar objects
- `count`: Total number of calendars

**REQ-LIST-006**: The tool shall handle authentication errors and return appropriate error messages.

### Tool 2: read_calendar_events

**REQ-READ-001**: The server shall provide a tool named `read_calendar_events` that reads events from a specified calendar within a date range.

**REQ-READ-002**: The tool shall accept optional parameters:

- `calendar_id`: Calendar ID (defaults to WBSO calendar if not provided)
- `calendar_name`: Calendar name to filter by (optional)
- `start_date`: Start date in ISO format (YYYY-MM-DD or ISO datetime)
- `end_date`: End date in ISO format (YYYY-MM-DD or ISO datetime)

**REQ-READ-003**: If `start_date` is not provided, the tool shall default to the current date.

**REQ-READ-004**: If `end_date` is not provided, the tool shall default to 30 days after `start_date`.

**REQ-READ-005**: The tool shall validate date formats and return errors for invalid formats.

**REQ-READ-006**: The tool shall convert date ranges to UTC for Google Calendar API calls.

**REQ-READ-007**: The tool shall return events sorted by start time.

**REQ-READ-008**: The tool shall return a JSON object with:

- `events`: Array of event objects with full details
- `count`: Total number of events found
- `calendar_id`: Calendar ID used for the query

**REQ-READ-009**: The tool shall handle HTTP errors from Google Calendar API and return structured error responses.

### Tool 3: summarize_calendar_events

**REQ-SUM-001**: The server shall provide a tool named `summarize_calendar_events` that provides summary statistics for events in a date range.

**REQ-SUM-002**: The tool shall accept the same parameters as `read_calendar_events` (calendar_id, calendar_name, start_date, end_date).

**REQ-SUM-003**: The tool shall calculate and return:

- `total_items`: Total number of events
- `total_days`: Number of unique days with events
- `total_hours`: Total duration of all events in hours (rounded to 2 decimal places)
- `date_range`: Earliest and latest event dates

**REQ-SUM-004**: The tool shall use `read_calendar_events` internally to retrieve events.

**REQ-SUM-005**: The tool shall handle errors from `read_calendar_events` and return appropriate error messages.

### Tool 4: create_calendar_event

**REQ-CREATE-001**: The server shall provide a tool named `create_calendar_event` that creates a calendar event object (without writing to calendar).

**REQ-CREATE-002**: The tool shall require the following parameters:

- `summary`: Event title/summary (required)
- `start_time`: Start time in ISO datetime format (required)
- `end_time`: End time in ISO datetime format (required)

**REQ-CREATE-003**: The tool shall accept optional parameters:

- `description`: Event description
- `calendar_id`: Target calendar ID (for validation, not used for creation)
- `location`: Event location (defaults to "Home Office")
- `extended_properties`: Extended properties for WBSO metadata

**REQ-CREATE-004**: The tool shall validate that `end_time` is after `start_time` and return an error if not.

**REQ-CREATE-005**: The tool shall parse datetime strings and handle timezone conversion to Amsterdam timezone.

**REQ-CREATE-006**: The tool shall return a JSON object with:

- `event`: Event object in Google Calendar format
- `message`: Indication that event is created but not yet written to calendar

**REQ-CREATE-007**: The tool shall return errors for invalid datetime formats or missing required parameters.

### Tool 5: write_calendar_events

**REQ-WRITE-001**: The server shall provide a tool named `write_calendar_events` that writes event objects to the calendar.

**REQ-WRITE-002**: The tool shall require:

- `events`: Array of event objects (required)

**REQ-WRITE-003**: The tool shall accept optional parameter:

- `calendar_id`: Target calendar ID (defaults to WBSO calendar if not provided)

**REQ-WRITE-004**: The tool shall validate that the target calendar is the WBSO calendar (REQ-SEC-002).

**REQ-WRITE-005**: The tool shall check that the target calendar has write permissions (REQ-SEC-003).

**REQ-WRITE-006**: The tool shall convert event dictionaries to `CalendarEvent` objects.

**REQ-WRITE-007**: The tool shall use the `GoogleCalendarUploader` to upload events with duplicate detection.

**REQ-WRITE-008**: The tool shall return a JSON object with:

- `success`: Boolean indicating overall success
- `uploaded_count`: Number of events successfully uploaded
- `errors`: Array of error messages (if any)
- `conversion_errors`: Array of conversion errors (if any)
- `session_mapping`: Mapping of session IDs to event IDs

**REQ-WRITE-009**: The tool shall log detailed information for each event being uploaded (summary, dates, location, target calendar).

**REQ-WRITE-010**: The tool shall handle upload failures and return detailed error information.

### Tool 6: detect_duplicates_conflicts

**REQ-DUP-001**: The server shall provide a tool named `detect_duplicates_conflicts` that detects duplicate events and conflicts (overlapping events).

**REQ-DUP-002**: The tool shall accept optional parameters:

- `calendar_id`: Calendar ID to check (defaults to WBSO calendar)
- `start_date`: Start date for date range (ISO format)
- `end_date`: End date for date range (ISO format)
- `events`: Optional array of events to check against existing calendar events

**REQ-DUP-003**: The tool shall detect duplicates by:

- Session ID (from extended properties)
- Exact datetime range (start and end times match)

**REQ-DUP-004**: The tool shall detect conflicts (overlapping events) by comparing event start/end times.

**REQ-DUP-005**: The tool shall return a JSON object with:

- `duplicates`: Object containing `by_session_id` and `by_datetime` arrays
- `conflicts`: Array of conflict objects with overlap details
- `summary`: Summary counts for duplicates and conflicts

**REQ-DUP-006**: The tool shall calculate overlap duration in hours for conflicts.

### Tool 7: edit_calendar_event

**REQ-EDIT-001**: The server shall provide a tool named `edit_calendar_event` that updates an existing calendar event.

**REQ-EDIT-002**: The tool shall require:

- `event_id`: Event ID to update (required)
- `updates`: Dictionary of fields to update (required)

**REQ-EDIT-003**: The tool shall accept optional parameter:

- `calendar_id`: Target calendar ID (defaults to WBSO calendar)

**REQ-EDIT-004**: The tool shall validate that the target calendar is the WBSO calendar (REQ-SEC-002).

**REQ-EDIT-005**: The tool shall check that the target calendar has write permissions (REQ-SEC-003).

**REQ-EDIT-006**: The tool shall retrieve the existing event before applying updates.

**REQ-EDIT-007**: The tool shall handle datetime updates by converting to Amsterdam timezone.

**REQ-EDIT-008**: The tool shall return the updated event object on success.

**REQ-EDIT-009**: The tool shall return an error if the event is not found.

**REQ-EDIT-010**: The tool shall return errors for invalid datetime formats in updates.

### Tool 8: delete_calendar_event

**REQ-DELETE-001**: The server shall provide a tool named `delete_calendar_event` that deletes a calendar event by ID.

**REQ-DELETE-002**: The tool shall require:

- `event_id`: Event ID to delete (required)

**REQ-DELETE-003**: The tool shall accept optional parameter:

- `calendar_id`: Target calendar ID (defaults to WBSO calendar)

**REQ-DELETE-004**: The tool shall validate that the target calendar is the WBSO calendar (REQ-SEC-002).

**REQ-DELETE-005**: The tool shall check that the target calendar has write permissions (REQ-SEC-003).

**REQ-DELETE-006**: The tool shall retrieve event information before deletion for logging.

**REQ-DELETE-007**: The tool shall return a success message with event summary on successful deletion.

**REQ-DELETE-008**: The tool shall return an error if the event is not found.

## References

- [src/mcp/calendar_server.py](src/mcp/calendar_server.py) - Implementation
- [src/wbso/calendar_security.py](src/wbso/calendar_security.py) - Security validation
- [src/wbso/upload.py](src/wbso/upload.py) - Event upload functionality
- [docs/project/hours/CALENDAR_SECURITY.md](docs/project/hours/CALENDAR_SECURITY.md) - Security model documentation
- [docs/technical/MCP_CALENDAR_SERVER.md](docs/technical/MCP_CALENDAR_SERVER.md) - Technical documentation
