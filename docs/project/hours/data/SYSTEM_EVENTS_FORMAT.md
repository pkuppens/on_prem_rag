# System Events Data Format

This document describes the system events CSV files used for WBSO hours registration to capture workstation activity when Git commit data may be insufficient.

## File Format

System events are stored in CSV format with the following columns:

| Column         | Type   | Description                                   | Example                                     |
| -------------- | ------ | --------------------------------------------- | ------------------------------------------- |
| DateTime       | String | Event timestamp in YYYY/MM/DD HH:MM:SS format | "2025/05/03 11:55:40"                       |
| EventId        | String | Windows Event Log event ID                    | "1074"                                      |
| LogName        | String | Event log source                              | "System"                                    |
| EventType      | String | Type of system event                          | "System shutdown/restart initiated"         |
| Level          | String | Event severity level                          | "Information", "Error", "Critical"          |
| Username       | String | User associated with the event                | "aigent-4090\piete"                         |
| ProcessName    | String | Process that triggered the event              | "Explorer.EXE"                              |
| Message        | String | Detailed event description                    | "The process Explorer.EXE has initiated..." |
| AdditionalInfo | String | Additional event details                      | "Reason: , Comment: "                       |
| RecordId       | String | Unique event record identifier                | "37527"                                     |

## Key Event Types

### System Activity Events

- **EventId 1074**: System shutdown/restart initiated
- **EventId 42**: System entering sleep
- **EventId 41**: System rebooted without cleanly shutting down
- **EventId 6008**: Unexpected shutdown
- **EventId 6005**: System startup (Event Log service started)
- **EventId 6006**: System shutdown (Event Log service stopped)
- **EventId 6013**: System uptime report

### Usage in WBSO Hours Registration

System events provide supplementary data to Git commit history for:

1. **Work Session Boundaries**: Identify when work sessions started and ended
2. **System Downtime**: Account for periods when the system was unavailable
3. **Activity Validation**: Corroborate Git commit timestamps with system activity
4. **Gap Analysis**: Identify periods of uncommitted work activity

### Data Processing

The system events data is processed to:

- Extract work session start/end times
- Calculate actual working hours
- Identify system maintenance periods
- Validate Git commit activity patterns

## File Naming Convention

Files follow the pattern: `system_events_YYYYMMDD.csv`

- `system_events_20250826.csv` - Events from August 26, 2025
- `system_events_20250821.csv` - Events from August 21, 2025

## Integration with WBSO Process

This data supplements the Git commit analysis by providing:

- **Complete Activity Picture**: Captures all system activity, not just committed work
- **Time Validation**: Verifies that Git commits occurred during active system periods
- **Work Pattern Analysis**: Identifies typical working hours and patterns
- **Compliance Support**: Provides audit trail for WBSO hour calculations

## Related Files

- [Extract-SystemEvents.ps1](../scripts/Extract-SystemEvents.ps1) - PowerShell script for extracting system events
- [Extract-SystemEvents.md](../scripts/Extract-SystemEvents.md) - Documentation for the extraction script
- [process_commits.py](../process_commits.py) - Main processing script that may integrate system events data
