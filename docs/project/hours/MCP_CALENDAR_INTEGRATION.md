# MCP Calendar Integration Guide

## Overview

This guide explains how to integrate the MCP Calendar Server with your WBSO hours registration workflow. The MCP server provides a standardized interface for managing Google Calendar events, enabling automation of calendar operations from git commits and computer logon/logoff events.

## Use Case

The underlying user need is to fill the WBSO calendar with entries generated from:

- **Git commits**: Extract commit history and create calendar events
- **Computer logon/logoff events**: Track work sessions and create calendar entries

These needs are explained in detail in the [WBSO Hours Registration documentation](HOURS_REGISTRATION.md).

## Prerequisites

1. **Google Calendar API Setup**

   - Follow the [Google Calendar API Setup Guide](scripts/setup_google_calendar_api.md)
   - Ensure `credentials.json` and `token.json` are configured
   - Verify access to the "WBSO Activities 2025" calendar

2. **MCP Server Installation**
   - MCP SDK is already included in project dependencies
   - Verify installation: `uv run python -c "import mcp; print('MCP installed')"`

## Quick Start

### 1. Start the MCP Server

```bash
# Option 1: Run as module
python -m mcp.calendar_server

# Option 2: Use standalone script
python scripts/start_mcp_calendar_server.py
```

### 2. Connect MCP Client

The MCP server uses stdio transport by default. Connect your MCP client to the server's stdin/stdout.

### 3. Use MCP Tools

Once connected, you can use any of the 8 available tools:

- `list_calendars`: List accessible calendars
- `read_calendar_events`: Read events by date range
- `summarize_calendar_events`: Get summary statistics
- `create_calendar_event`: Create event objects
- `write_calendar_events`: Write events to calendar
- `detect_duplicates_conflicts`: Check for duplicates/conflicts
- `edit_calendar_event`: Update existing events
- `delete_calendar_event`: Remove events

## Integration Examples

### Example 1: Create Events from Git Commits

```python
# Pseudo-code example
from mcp.client import MCPClient

client = MCPClient()

# 1. Read git commits
commits = extract_git_commits(repository_path, start_date, end_date)

# 2. Create calendar events for each commit session
events = []
for commit_session in commits:
    event = client.call_tool("create_calendar_event", {
        "summary": f"WBSO: {commit_session.category} - {commit_session.type}",
        "start_time": commit_session.start_time.isoformat(),
        "end_time": commit_session.end_time.isoformat(),
        "description": commit_session.description,
        "extended_properties": {
            "private": {
                "session_id": commit_session.id,
                "wbso_category": commit_session.category,
                "work_hours": str(commit_session.hours)
            }
        }
    })
    events.append(event["event"])

# 3. Check for duplicates before writing
duplicates = client.call_tool("detect_duplicates_conflicts", {
    "start_date": start_date.isoformat(),
    "end_date": end_date.isoformat(),
    "events": events
})

if duplicates["summary"]["duplicate_session_ids"] == 0:
    # 4. Write events to calendar
    result = client.call_tool("write_calendar_events", {
        "events": events
    })
    print(f"Uploaded {result['uploaded_count']} events")
else:
    print(f"Found {duplicates['summary']['duplicate_session_ids']} duplicates, skipping upload")
```

### Example 2: Summarize WBSO Hours

```python
# Get summary for typical date range
summary = client.call_tool("summarize_calendar_events", {
    "calendar_name": "WBSO Activities 2025",
    "start_date": "2025-06-01",
    "end_date": "2025-12-31"
})

print(f"Total Items: {summary['total_items']}")
print(f"Total Days: {summary['total_days']}")
print(f"Total Hours: {summary['total_hours']}")
```

### Example 3: Process Logon/Logoff Events

```python
# Process system events and create calendar entries
logon_events = extract_logon_events(start_date, end_date)

for session in detect_work_sessions(logon_events):
    # Check if event already exists
    existing = client.call_tool("read_calendar_events", {
        "start_date": session.start_time.isoformat(),
        "end_date": session.end_time.isoformat()
    })

    # Check for duplicates
    if not is_duplicate(session, existing["events"]):
        # Create and write event
        event = client.call_tool("create_calendar_event", {
            "summary": f"WBSO: {session.category}",
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "extended_properties": {
                "private": {
                    "session_id": session.id,
                    "source_type": "system_events"
                }
            }
        })

        client.call_tool("write_calendar_events", {
            "events": [event["event"]]
        })
```

## Testing

### Run Integration Tests

The test suite creates dummy events in December 2024 (out of scope for 2025 WBSO project) to verify all functionality:

```bash
uv run pytest tests/test_mcp_calendar_server.py -v -m internet
```

### Generate Test Report

After running tests, generate a comprehensive markdown report:

```bash
python src/mcp/test_report_generator.py tests/test_results_mcp_calendar.json tests/test_report_mcp_calendar.md
```

The report includes:

- Test summary (total tests, passed, failed)
- Per-tool test results
- Expected vs actual outcomes
- Error details
- Recommendations

## Configuration

### Environment Variables

```bash
# Custom credentials paths
export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
export GOOGLE_TOKEN_PATH=/path/to/token.json

# Run server
python -m mcp.calendar_server
```

### Default Paths

If environment variables are not set, the server uses:

- Credentials: `docs/project/hours/scripts/credentials.json`
- Token: `docs/project/hours/scripts/token.json`

## Workflow Integration

### Step 1: Extract Data Sources

1. **Git Commits**: Use existing scripts in `docs/project/hours/scripts/`
2. **System Events**: Extract logon/logoff events
3. **GitHub Issues**: Track issue-related work

### Step 2: Process and Categorize

1. Group commits/events into work sessions
2. Categorize as WBSO-eligible activities
3. Calculate work hours per session

### Step 3: Create Calendar Events

1. Use `create_calendar_event` to create event objects
2. Include WBSO metadata in `extended_properties`
3. Validate event data

### Step 4: Check for Duplicates

1. Use `detect_duplicates_conflicts` before writing
2. Skip events that already exist
3. Handle conflicts appropriately

### Step 5: Write to Calendar

1. Use `write_calendar_events` to upload events
2. Monitor upload results
3. Handle errors gracefully

### Step 6: Verify and Report

1. Use `read_calendar_events` to verify uploads
2. Use `summarize_calendar_events` for reporting
3. Generate compliance reports

## Troubleshooting

### Authentication Issues

**Problem**: "Credentials file not found"

**Solution**:

1. Ensure `credentials.json` exists in the expected location
2. Set `GOOGLE_CREDENTIALS_PATH` environment variable
3. Follow [Google Calendar API Setup Guide](scripts/setup_google_calendar_api.md)

### Calendar Not Found

**Problem**: "WBSO calendar not found"

**Solution**:

1. Verify calendar exists: Use `list_calendars` tool
2. Check calendar name matches "WBSO Activities 2025"
3. Ensure you have write access to the calendar

### Duplicate Detection Issues

**Problem**: Duplicates not detected correctly

**Solution**:

1. Check `session_id` in `extended_properties.private`
2. Verify datetime ranges are exact matches
3. Review `detect_duplicates_conflicts` output

### Event Upload Failures

**Problem**: Events fail to upload

**Solution**:

1. Check event validation: Ensure all required fields present
2. Verify calendar permissions: Must be "owner" or "writer"
3. Check rate limits: Server includes rate limiting
4. Review error messages in upload results

## Best Practices

1. **Always Check for Duplicates**: Use `detect_duplicates_conflicts` before writing events
2. **Validate Events**: Ensure events have required WBSO metadata
3. **Handle Errors**: Implement proper error handling in integration code
4. **Monitor Uploads**: Check upload results and handle failures
5. **Regular Summaries**: Use `summarize_calendar_events` for progress tracking
6. **Test First**: Use December 2024 for testing (out of scope for 2025 project)

## Related Documentation

- [MCP Calendar Server Technical Documentation](../../technical/MCP_CALENDAR_SERVER.md)
- [WBSO Hours Registration](HOURS_REGISTRATION.md)
- [Google Calendar Integration Summary](GOOGLE_CALENDAR_INTEGRATION_SUMMARY.md)
- [Google Calendar API Setup Guide](scripts/setup_google_calendar_api.md)

## Code Files

- [src/mcp/calendar_server.py](../../src/mcp/calendar_server.py) - MCP server implementation
- [src/wbso/upload.py](../../src/wbso/upload.py) - Google Calendar upload functionality
- [src/wbso/calendar_event.py](../../src/wbso/calendar_event.py) - Calendar event data models
- [tests/test_mcp_calendar_server.py](../../tests/test_mcp_calendar_server.py) - Integration tests
