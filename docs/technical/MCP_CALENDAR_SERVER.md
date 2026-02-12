# MCP Calendar Server Technical Documentation

## Overview

The MCP Calendar Server is a Model Context Protocol (MCP) server that exposes Google Calendar functionality for WBSO hours registration. It provides comprehensive calendar management capabilities including read, write, edit, delete, conflict detection, and event summarization.

## Architecture

### Components

1. **MCP Server Core** (`src/mcp/calendar_server.py`)
   - Implements MCP protocol handlers
   - Manages tool registration and execution
   - Integrates with existing `GoogleCalendarUploader` class
   - Handles authentication and error management

2. **Test Suite** (`tests/test_mcp_calendar_server.py`)
   - Integration tests for all calendar operations
   - Creates dummy events in December 2024 (out of scope for 2025 WBSO project)
   - Verifies CRUD operations, duplicate detection, and summarization

3. **Test Report Generator** (`src/mcp/test_report_generator.py`)
   - Generates markdown test reports
   - Compares test results vs expected outcomes
   - Documents pass/fail status for each operation

## MCP Tools

### 1. list_calendars

Lists all accessible Google Calendars with their IDs, names, and access roles.

**Input**: None

**Output**:
```json
{
  "calendars": [
    {
      "id": "calendar_id",
      "summary": "Calendar Name",
      "accessRole": "owner",
      "description": "Calendar description",
      "timeZone": "Europe/Amsterdam"
    }
  ],
  "count": 1
}
```

### 2. read_calendar_events

Reads calendar events by calendar name, date range, or calendar ID.

**Input**:
- `calendar_id` (optional): Calendar ID (defaults to WBSO calendar)
- `calendar_name` (optional): Calendar name to filter by
- `start_date` (optional): Start date in ISO format (defaults to 30 days ago)
- `end_date` (optional): End date in ISO format (defaults to 30 days from now)

**Output**:
```json
{
  "events": [...],
  "count": 10,
  "calendar_id": "calendar_id"
}
```

### 3. summarize_calendar_events

Summarizes calendar events with total count, number of unique days, and total hours.

**Input**: Same as `read_calendar_events`

**Output**:
```json
{
  "total_items": 10,
  "total_days": 5,
  "total_hours": 20.5,
  "date_range": {
    "earliest": "2024-12-01T00:00:00",
    "latest": "2024-12-31T23:59:59"
  }
}
```

### 4. create_calendar_event

Creates a calendar event (dummy for testing). Returns event object that can be written to calendar.

**Input**:
- `summary` (required): Event title/summary
- `start_time` (required): Start time in ISO datetime format
- `end_time` (required): End time in ISO datetime format
- `description` (optional): Event description
- `calendar_id` (optional): Target calendar ID
- `location` (optional): Event location
- `extended_properties` (optional): Extended properties for WBSO metadata

**Output**:
```json
{
  "event": {...},
  "message": "Event created (not yet written to calendar). Use write_calendar_events to write it."
}
```

### 5. write_calendar_events

Writes created calendar events directly to the calendar.

**Input**:
- `events` (required): List of event objects (from `create_calendar_event` or external)
- `calendar_id` (optional): Target calendar ID

**Output**:
```json
{
  "success": true,
  "uploaded_count": 3,
  "errors": [],
  "session_mapping": {...}
}
```

### 6. detect_duplicates_conflicts

Detects duplicate events and conflicts (overlapping events) in calendar.

**Input**:
- `calendar_id` (optional): Target calendar ID
- `start_date` (optional): Date range start in ISO format
- `end_date` (optional): Date range end in ISO format
- `events` (optional): List of events to check against existing calendar events

**Output**:
```json
{
  "duplicates": {
    "by_session_id": [...],
    "by_datetime": [...]
  },
  "conflicts": [...],
  "summary": {
    "duplicate_session_ids": 0,
    "duplicate_datetime_ranges": 0,
    "conflicts": 0
  }
}
```

### 7. edit_calendar_event

Edits an existing calendar event. Updates specified fields.

**Input**:
- `calendar_id` (optional): Target calendar ID
- `event_id` (required): Event ID to update
- `updates` (required): Dictionary of fields to update (summary, description, start, end, etc.)

**Output**:
```json
{
  "success": true,
  "event_id": "event_id",
  "updated_fields": ["summary", "description"],
  "event": {...}
}
```

### 8. delete_calendar_event

Deletes a calendar event by ID.

**Input**:
- `calendar_id` (optional): Target calendar ID
- `event_id` (required): Event ID to delete

**Output**:
```json
{
  "success": true,
  "event_id": "event_id",
  "message": "Event deleted successfully"
}
```

## Authentication

The MCP server reuses the existing authentication flow from `GoogleCalendarUploader`:

1. Load existing token from `token.json`
2. Refresh if expired
3. Run OAuth flow if needed
4. Store credentials for future use

### Configuration

Credentials paths can be configured via environment variables:
- `GOOGLE_CREDENTIALS_PATH`: Path to OAuth credentials JSON file
- `GOOGLE_TOKEN_PATH`: Path to OAuth token JSON file

Default paths:
- Credentials: `docs/project/hours/scripts/credentials.json`
- Token: `docs/project/hours/scripts/token.json`

## Error Handling

All Google Calendar API calls are wrapped in try/except blocks:
- HTTP errors are converted to MCP error responses
- Errors are logged for debugging
- User-friendly error messages are returned

## Data Model Compatibility

The server uses existing `CalendarEvent` dataclass from `src/wbso/calendar_event.py`:
- Converts between MCP tool inputs/outputs and `CalendarEvent` objects
- Maintains WBSO metadata in `extended_properties`
- Validates event data before operations

## Running the Server

### As a Module

```bash
python -m mcp.calendar_server
```

### Using Standalone Script

```bash
python scripts/start_mcp_calendar_server.py [--transport stdio|http] [--port PORT] [--credentials-path PATH] [--token-path PATH]
```

### Environment Variables

```bash
export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
export GOOGLE_TOKEN_PATH=/path/to/token.json
python -m mcp.calendar_server
```

## Testing

### Running Integration Tests

```bash
uv run pytest tests/test_mcp_calendar_server.py -v -m internet
```

### Generating Test Report

After running tests, generate a markdown report:

```bash
python src/mcp/test_report_generator.py tests/test_results_mcp_calendar.json tests/test_report_mcp_calendar.md
```

## Dependencies

- `mcp>=1.0.0`: Official MCP Python SDK
- `google-api-python-client>=2.179.0`: Google Calendar API client
- `google-auth-oauthlib>=1.2.2`: OAuth2 authentication
- `google-auth-httplib2>=0.2.0`: HTTP transport for authentication

## Code Files

- [src/mcp/calendar_server.py](src/mcp/calendar_server.py) - Main MCP server implementation
- [src/mcp/test_report_generator.py](src/mcp/test_report_generator.py) - Test report generation
- [src/mcp/__main__.py](src/mcp/__main__.py) - Module entry point
- [tests/test_mcp_calendar_server.py](tests/test_mcp_calendar_server.py) - Integration tests
- [scripts/start_mcp_calendar_server.py](scripts/start_mcp_calendar_server.py) - Standalone startup script

## References

- [Model Context Protocol](https://modelcontextprotocol.io/introduction)
- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [WBSO Upload Module](../src/wbso/upload.py)
- [WBSO Calendar Event Models](../src/wbso/calendar_event.py)
