# WBSO Data Flow Documentation

**Document Version**: 1.0  
**Created**: 2025-11-28  
**Last Updated**: 2025-11-28

## Overview

This document describes the complete data flow for WBSO hours registration, from raw data collection through calendar upload and reporting. The pipeline is designed to be automated, programmatic, and suitable for AI agent orchestration.

## Pipeline Architecture

The WBSO data pipeline consists of the following stages:

1. **Data Collection** - Gather raw data from multiple sources
2. **Data Processing** - Process and normalize raw data
3. **Session Generation** - Create work sessions from processed data
4. **Time Polishing** - Round times and add breaks
5. **Deduplication** - Remove duplicate sessions
6. **Conflict Detection** - Identify calendar conflicts
7. **Event Description** - Generate WBSO-worthy descriptions
8. **Calendar Upload** - Upload to Google Calendar (without duplication)
9. **Reporting** - Generate compliance reports

## Stage 1: Data Collection

### Purpose
Collect raw data from all available sources for WBSO hours tracking.

### Inputs
- None (initial data collection)

### Processes

#### 1.1 Computer Session Data Collection
- **Source**: System event logs (computer on/off events)
- **Script**: `docs/project/hours/scripts/Extract-SystemEvents.ps1` (Windows)
- **Output**: `docs/project/hours/data/system_events_YYYYMMDD.csv`
- **Frequency**: Daily or on-demand
- **Validation**: 
  - Verify file exists and is readable
  - Check for required columns: timestamp, event_type, computer_name
  - Validate timestamp format

#### 1.2 Git Commit Data Collection
- **Source**: Git repositories (commit history)
- **Script**: `docs/project/hours/scripts/extract_git_commits.ps1`
- **Output**: `docs/project/hours/data/commits/{repository_name}.csv`
- **Frequency**: Daily or on-demand
- **Repositories**: Multiple repositories tracked (see `data/repositories.csv`)
- **Validation**:
  - Verify repository exists and is accessible
  - Check for required columns: timestamp, author, message, hash
  - Validate commit timestamps

### Outputs
- `data/system_events_*.csv` - Computer session logs
- `data/commits/*.csv` - Git commit history per repository
- `data/repositories.csv` - Repository configuration

### Upstream Triggers
- Manual execution
- Scheduled daily/weekly runs
- AI agent orchestration

### Downstream Events
- Triggers Stage 2: Data Processing

---

## Stage 2: Data Processing

### Purpose
Process and normalize raw data into a consistent format.

### Inputs
- `data/system_events_*.csv`
- `data/commits/*.csv`

### Processes

#### 2.1 System Events Processing
- **Script**: `docs/project/hours/scripts/analyze_system_events.py`
- **Process**:
  - Parse CSV files
  - Identify computer-on sessions (work blocks)
  - Calculate session durations
  - Filter for WBSO-eligible time periods (2025-06-01 onwards)
- **Output**: `data/all_system_events_processed.json`

#### 2.2 Git Commits Processing
- **Script**: `docs/project/hours/scripts/process_commits.py`
- **Process**:
  - Parse commit CSV files
  - Standardize timestamps
  - Filter for WBSO-eligible authors
  - Extract commit metadata
- **Output**: `data/commits_processed.json`

### Outputs
- `data/all_system_events_processed.json` - Processed system events
- `data/commits_processed.json` - Processed git commits

### Upstream Triggers
- Completion of Stage 1: Data Collection
- Manual execution with `--force-refresh` flag

### Downstream Events
- Triggers Stage 3: Session Generation

---

## Stage 3: Session Generation

### Purpose
Generate work sessions from processed data, combining system events and git commits.

### Inputs
- `data/all_system_events_processed.json`
- `data/commits_processed.json`

### Processes

#### 3.1 Real Session Generation
- **Script**: `docs/project/hours/scripts/generate_work_sessions.py`
- **Process**:
  - Match commits to system event sessions
  - Assign commits to work sessions
  - Apply WBSO eligibility rules
  - Calculate work hours (excluding breaks)
- **Output**: `data/work_log.json`

#### 3.2 Synthetic Session Generation
- **Script**: `docs/project/hours/scripts/generate_synthetic_sessions.py`
- **Process**:
  - Identify unassigned commits (not matched to system events)
  - Generate synthetic sessions for unassigned commits
  - Apply morning/afternoon/evening templates with variation
  - Categorize by WBSO activity type
- **Output**: `data/synthetic_sessions.json`

#### 3.3 Session Merging
- **Script**: `docs/project/hours/scripts/merge_work_sessions.py`
- **Process**:
  - Combine real and synthetic sessions
  - Remove duplicate sessions
  - Create unified work log
- **Output**: `data/work_log_complete.json`

### Outputs
- `data/work_log.json` - Real sessions from system events
- `data/synthetic_sessions.json` - Synthetic sessions from unassigned commits
- `data/work_log_complete.json` - Combined work log

### Upstream Triggers
- Completion of Stage 2: Data Processing
- Manual execution

### Downstream Events
- Triggers Stage 4: Time Polishing

---

## Stage 4: Time Polishing

### Purpose
Round times to 5-minute intervals and add breaks to full-day sessions.

### Inputs
- `data/work_log_complete.json`

### Processes

#### 4.1 Time Rounding
- **Function**: `src/wbso/time_utils.round_to_quarter_hour()`
- **Process**:
  - Round start and end times to nearest 5-minute interval
  - Special handling: 57-59 minutes → 0 (next hour)
  - Preference for quarter hours (0, 15, 30, 45)
- **Rules**:
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

#### 4.2 Synthetic Session Time Variation
- **Function**: `src/wbso/time_utils.add_deterministic_variation()`
- **Process**:
  - Add ±5-10 minutes variation to 20% of synthetic sessions
  - Use deterministic random number generator (seed = session_id)
  - Morning sessions: 08:45-12:30 (base) with variation
  - Afternoon sessions: 13:00-17:15 (base) with variation
- **Purpose**: Make synthetic sessions more realistic

#### 4.3 Break Addition
- **Functions**: 
  - `src/wbso/time_utils.generate_lunch_break()`
  - `src/wbso/time_utils.generate_dinner_break()`
- **Process**:
  - Identify full_day sessions
  - Add lunch break: 12:00, 12:15, or 12:30 start, 25-40 minutes duration
  - Add dinner break: 17:30-18:15 start (5-minute intervals), 30-50 minutes duration
  - Recalculate work_hours excluding breaks
- **Output**: Updated sessions with breaks and adjusted work_hours

### Outputs
- `data/work_log_polished.json` - Sessions with rounded times and breaks

### Upstream Triggers
- Completion of Stage 3: Session Generation
- Manual execution with `--polish-times` flag

### Downstream Events
- Triggers Stage 5: Deduplication

---

## Stage 5: Deduplication

### Purpose
Remove duplicate sessions based on session_id and datetime ranges.

### Inputs
- `data/work_log_polished.json`

### Processes

#### 5.1 Session ID Deduplication
- **Function**: `src/wbso/validation.WBSODataValidator.validate_duplicates()`
- **Process**:
  - Identify sessions with duplicate session_ids
  - Keep first occurrence, mark others as duplicates
  - Log duplicate detection results

#### 5.2 DateTime Range Deduplication
- **Function**: `src/wbso/validation.WBSODataValidator.validate_duplicates()`
- **Process**:
  - Identify sessions with identical start_time and end_time
  - Keep first occurrence, mark others as duplicates
  - Handle special case: Morning/Afternoon/Evening sessions on same date

#### 5.3 Synthetic Session Deduplication
- **Special Handling**:
  - Check for duplicate Morning/Afternoon/Evening sessions on same date
  - Ensure only one session per type per date
  - Use session_id as primary key for deduplication

### Outputs
- `validation_output/cleaned_dataset.json` - Deduplicated sessions
- `validation_output/duplicate_sessions.json` - Duplicate detection report

### Upstream Triggers
- Completion of Stage 4: Time Polishing
- Manual execution

### Downstream Events
- Triggers Stage 6: Conflict Detection

---

## Stage 6: Conflict Detection

### Purpose
Detect conflicts between WBSO sessions and existing calendar events.

### Inputs
- `validation_output/cleaned_dataset.json`
- Existing Google Calendar events (queried via API)

### Processes

#### 6.1 Calendar Event Query
- **Function**: `src/wbso/upload.GoogleCalendarUploader.get_existing_events()`
- **Process**:
  - Query Google Calendar API for existing events
  - Filter by date range (2025-06-01 to today)
  - Build indexes by session_id and datetime range

#### 6.2 Conflict Detection
- **Function**: `src/wbso/upload.GoogleCalendarUploader.create_upload_plan()`
- **Process**:
  - Compare WBSO sessions with existing calendar events
  - Detect time overlaps
  - Classify conflicts: short (<2 hours) vs long (≥2 hours)
  - Check for duplicate session_ids in calendar
  - Check for duplicate datetime ranges in calendar

#### 6.3 Conflict Resolution
- **Automatic Resolution** (short conflicts < 2 hours):
  - Adjust WBSO session times to avoid conflicts
  - Log adjustments
- **Manual Review** (long conflicts ≥ 2 hours):
  - Flag for manual review
  - Generate conflict report

### Outputs
- `validation_output/calendar_conflict_reports.json` - Conflict detection results
- Upload plan with conflict resolution

### Upstream Triggers
- Completion of Stage 5: Deduplication
- Manual execution

### Downstream Events
- Triggers Stage 7: Event Description

---

## Stage 7: Event Description

### Purpose
Generate WBSO-worthy descriptions for calendar events.

### Inputs
- `validation_output/cleaned_dataset.json`

### Processes

#### 7.1 Description Generation
- **Function**: `src/wbso/calendar_event.CalendarEvent.from_wbso_session()`
- **Process**:
  - Generate category-specific WBSO descriptions
  - Include technical work performed
  - Add session details (type, duration, date)
  - Include source information (real vs synthetic)
  - Add WBSO eligibility statement

#### 7.2 Title Generation
- **Process**:
  - Remove "WBSO:" prefix (implicit from calendar name)
  - Format: "{Category} - {Session Type}"
  - Example: "AI Framework - Morning"

#### 7.3 Category Descriptions
- **AI_FRAMEWORK**: "Development and implementation of AI agent frameworks, natural language processing capabilities, and intelligent communication systems for data-secure environments."
- **ACCESS_CONTROL**: "Research and development of authentication and authorization systems, security mechanisms, and access control protocols for privacy-preserving applications."
- **PRIVACY_CLOUD**: "Development of privacy-preserving cloud integration solutions, data protection mechanisms, and secure cloud communication protocols."
- **AUDIT_LOGGING**: "Implementation of comprehensive audit logging systems, privacy-friendly monitoring solutions, and compliance tracking mechanisms."
- **DATA_INTEGRITY**: "Research and development of data integrity protection systems, corruption prevention mechanisms, and validation frameworks."
- **GENERAL_RD**: "General research and development activities supporting the WBSO-AICM-2025-01 project objectives."

### Outputs
- Calendar events with WBSO-worthy descriptions

### Upstream Triggers
- Completion of Stage 6: Conflict Detection
- Manual execution

### Downstream Events
- Triggers Stage 8: Calendar Upload

---

## Stage 8: Calendar Upload

### Purpose
Upload WBSO calendar events to Google Calendar without duplication.

### Inputs
- Calendar events from Stage 7
- Existing calendar events (from Stage 6)

### Processes

#### 8.1 Upload Plan Creation
- **Function**: `src/wbso/upload.GoogleCalendarUploader.create_upload_plan()`
- **Process**:
  - Check for duplicate session_ids (existing calendar + upload batch)
  - Check for duplicate datetime ranges (existing calendar + upload batch)
  - Create upload plan: new_events, skip_events
  - Log skip reasons

#### 8.2 Batch Upload
- **Function**: `src/wbso/upload.GoogleCalendarUploader.upload_events_batch()`
- **Process**:
  - Upload events in batches of 50
  - Rate limiting: 0.1s delay between events
  - Retry logic: 3 attempts with exponential backoff
  - Progress tracking: real-time status updates

#### 8.3 Error Handling
- **Process**:
  - Log all errors with details
  - Retry failed uploads automatically
  - Report upload failures
  - Zero silent failures

### Outputs
- Calendar events in Google Calendar
- `upload_output/upload_log.json` - Upload results
- `upload_output/session_to_event_mapping.json` - session_id → google_event_id mapping

### Upstream Triggers
- Completion of Stage 7: Event Description
- Manual execution via `wbso-pipeline` command

### Downstream Events
- Triggers Stage 9: Reporting

---

## Stage 9: Reporting

### Purpose
Generate comprehensive WBSO compliance reports.

### Inputs
- Calendar events in Google Calendar
- `validation_output/cleaned_dataset.json`

### Processes

#### 9.1 Hours Calculation
- **Function**: `src/wbso/reporting.WBSOReporter.calculate_wbso_hours()`
- **Process**:
  - Query calendar for events in date range
  - Calculate total hours from calendar events
  - Compare with calculated hours from data
  - Generate gap analysis (current vs target 510 hours)

#### 9.2 Report Generation
- **Function**: `src/wbso/reporting.WBSOReporter.generate_compliance_documentation()`
- **Process**:
  - Generate category breakdown
  - Generate monthly/weekly breakdowns
  - Create compliance documentation
  - Export to CSV, JSON, and Markdown formats

#### 9.3 Verification Report
- **Function**: `src/wbso/pipeline.WBSOCalendarPipeline.step_4_verify()`
- **Process**:
  - Query calendar to verify events exist
  - Calculate hours from calendar
  - Compare with calculated hours
  - Generate verification report

### Outputs
- `reporting_output/wbso_hours_report.json` - Hours calculation
- `reporting_output/wbso_summary_report.md` - Human-readable summary
- `reporting_output/wbso_category_summary.csv` - Category breakdown
- `reporting_output/wbso_monthly_summary.csv` - Monthly breakdown
- `upload_output/pipeline_report.json` - Complete pipeline report

### Upstream Triggers
- Completion of Stage 8: Calendar Upload
- Manual execution via `wbso-report` command

### Downstream Events
- None (final stage)

---

## Complete Pipeline Execution

### Unified Pipeline Command
```bash
uv run wbso-pipeline
```

### Pipeline Steps (Automated)
1. **Data Collection** (if `--force-refresh` flag)
2. **Data Processing** (if data collection ran)
3. **Session Generation** (if data processing ran)
4. **Time Polishing** (automatic)
5. **Deduplication** (automatic)
6. **Conflict Detection** (automatic)
7. **Event Description** (automatic)
8. **Calendar Upload** (automatic)
9. **Reporting** (automatic)

### Manual Stage Execution
```bash
# Stage 1: Data Collection
# Run PowerShell scripts manually or via scheduler

# Stage 2: Data Processing
python docs/project/hours/scripts/analyze_system_events.py
python docs/project/hours/scripts/process_commits.py

# Stage 3: Session Generation
python docs/project/hours/scripts/generate_work_sessions.py
python docs/project/hours/scripts/generate_synthetic_sessions.py
python docs/project/hours/scripts/merge_work_sessions.py

# Stage 4-9: Unified Pipeline
uv run wbso-pipeline
```

## Input/Output Validation

### Stage Input Validation
Each stage validates its inputs:
- **File existence**: Check required input files exist
- **Format validation**: Verify JSON/CSV format is correct
- **Required fields**: Check for required data fields
- **Date range**: Validate dates are within target period (2025-06-01 onwards)

### Stage Output Validation
Each stage validates its outputs:
- **File creation**: Verify output files are created
- **Data integrity**: Check output data is valid
- **Completeness**: Verify all expected records are present
- **Format compliance**: Ensure output matches expected format

## Error Handling

### Validation Errors
- **Action**: Log error, stop pipeline, report issue
- **Recovery**: Fix data source, re-run failed stage

### Upload Errors
- **Action**: Log error, retry with exponential backoff
- **Recovery**: Automatic retry (3 attempts), manual retry if needed

### Conflict Errors
- **Action**: Log conflict, generate report
- **Recovery**: Automatic resolution (short conflicts), manual review (long conflicts)

## Pipeline Orchestration

### Current Implementation
- **Tool**: Custom Python pipeline (`src/wbso/pipeline.py`)
- **Orchestration**: Sequential execution with error handling
- **State Tracking**: File-based (output files indicate stage completion)

### Future Considerations
- **Luigi/Prefect**: Could be used for more complex orchestration
- **Current Assessment**: Custom pipeline is sufficient for current needs
- **Scalability**: Can migrate to Luigi/Prefect if pipeline complexity increases

## Monitoring and Logging

### Logging
- All stages log to `openagents.log`
- Log levels: INFO, WARNING, ERROR
- Structured logging with timestamps

### Monitoring
- Pipeline completion status
- Hours progress toward 510-hour target
- Upload success/failure rates
- Duplicate detection statistics

## Data Flow Diagram

```
[Data Sources]
    │
    ├─→ [System Events] ─→ [Process] ─→ [Real Sessions]
    │
    └─→ [Git Commits] ─→ [Process] ─→ [Synthetic Sessions]
                            │
                            └─→ [Merge] ─→ [Work Log]
                                            │
                                            ├─→ [Time Polish] ─→ [Deduplicate]
                                            │                        │
                                            │                        └─→ [Conflict Detect]
                                            │                              │
                                            │                              └─→ [Event Description]
                                            │                                    │
                                            │                                    └─→ [Calendar Upload]
                                            │                                          │
                                            │                                          └─→ [Reporting]
```

## Code Files

- [src/wbso/pipeline.py](src/wbso/pipeline.py) - Unified pipeline orchestration
- [src/wbso/time_utils.py](src/wbso/time_utils.py) - Time rounding and break generation utilities
- [src/wbso/calendar_event.py](src/wbso/calendar_event.py) - Calendar event creation and description generation
- [src/wbso/upload.py](src/wbso/upload.py) - Calendar upload with duplicate detection
- [src/wbso/validation.py](src/wbso/validation.py) - Data validation and deduplication
- [src/wbso/reporting.py](src/wbso/reporting.py) - Report generation
- [docs/project/hours/scripts/generate_synthetic_sessions.py](docs/project/hours/scripts/generate_synthetic_sessions.py) - Synthetic session generation
- [docs/project/hours/scripts/analyze_system_events.py](docs/project/hours/scripts/analyze_system_events.py) - System events processing

## References

- [TOC.md](TOC.md) - Theory of Constraints analysis
- [WBSO_PROCESS_RUNBOOK.md](WBSO_PROCESS_RUNBOOK.md) - Process runbook
- [PROJECT_PLAN.md](PROJECT_PLAN.md) - Project planning
