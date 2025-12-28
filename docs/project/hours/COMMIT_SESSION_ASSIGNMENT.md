# Commit-to-Session Assignment Implementation

**Created**: 2025-11-28  
**Updated**: 2025-11-28

## Overview

This document describes the implementation of commit-to-session assignment in the WBSO pipeline. This addresses the bottleneck of connecting commits to sessions to calculate WBSO hours more accurately.

## Problem Statement

The WBSO pipeline needs to:

1. Connect git commits to work sessions based on timestamps
2. Handle commits that fall outside session time ranges
3. Report hours in sessions with commits assigned
4. Export a mapping file for easy analysis

## Solution

### New Pipeline Step: `step_assign_commits_to_sessions`

**Location**: `src/wbso/pipeline_steps.py`

**Functionality**:

1. **Loads all commits** from CSV files (grouped by repository)
2. **Assigns commits to sessions** based on timestamp:
   - If commit timestamp falls within session time range (`start_time <= commit_time <= end_time`), assign to that session
   - If commit timestamp falls outside all sessions, assign to both:
     - Previous session (last session that ends before the commit)
     - Next session (first session that starts after the commit)
3. **Updates sessions** with commit messages and counts
4. **Exports mapping** to JSON file: `validation_output/session_commits_mapping.json`

### Assignment Logic

#### First Pass: Commits Within Sessions

- For each commit, check if its timestamp falls within any session's time range
- If yes, assign commit message to that session
- Track assigned commits to avoid duplicates

#### Second Pass: Commits Outside Sessions

- For commits not assigned in first pass:
  - Find the previous session (last session ending before commit)
  - Find the next session (first session starting after commit)
  - Assign commit message to both sessions (if they exist)

### Output Files

#### `validation_output/session_commits_mapping.json`

Format:

```json
{
  "session_id_1": ["Commit message 1", "Commit message 2"],
  "session_id_2": ["Commit message 3"]
}
```

This file can be easily merged with session data (start_time, end_time) to calculate WBSO hours.

### Reporting Updates

The `step_report` function now includes:

- `sessions_with_commits`: Number of sessions that have commits assigned
- `hours_with_commits`: Total hours in sessions with commits (filtered by date range)

These metrics appear in:

- Pipeline console output
- Step report data
- Final summary report

## Pipeline Integration

The new step is inserted into the pipeline after `step_assign_activities` and before `step_detect_commits_without_system_events`:

```python
step_assign_activities,  # Assign WBSO activities based on commits and repo purpose
step_assign_commits_to_sessions,  # Assign commits to sessions by timestamp
step_detect_commits_without_system_events,  # Detect commits on days without system events
```

## Usage

The step runs automatically as part of the WBSO pipeline:

```bash
uv run wbso-pipeline
```

### Output

The pipeline will:

1. Assign commits to sessions
2. Log statistics:
   - Number of commits assigned
   - Number of sessions with commits
   - Total hours in sessions with commits
   - Number of commits outside sessions
3. Export `session_commits_mapping.json` to `validation_output/`
4. Include commit statistics in the final report

### Example Output

```
STEP: ASSIGN COMMITS TO SESSIONS
============================================================
✅ Commit assignment complete:
   - 245 commits assigned to sessions
   - 180 sessions have commits assigned
   - 320.5 hours in sessions with commits
   - 15 commits outside sessions (assigned to adjacent sessions)
   - Mapping exported to: docs/project/hours/validation_output/session_commits_mapping.json
```

## Benefits

1. **Accurate Hour Calculation**: Only count hours in sessions with actual development work (commits)
2. **Easy Analysis**: JSON mapping file can be easily merged with session data
3. **Comprehensive Coverage**: Commits outside sessions are still assigned to adjacent sessions
4. **Reporting**: Pipeline report shows hours in sessions with commits

## Next Steps

1. Run the pipeline to generate the commit-to-session mapping
2. Analyze `session_commits_mapping.json` to identify:
   - Sessions without commits (may need synthetic sessions)
   - Commits that couldn't be assigned (work on different computers)
3. Use the mapping to calculate WBSO hours more accurately
4. Identify gaps where commits exist but sessions don't (potential missing hours)

## Code Files

- [src/wbso/pipeline_steps.py](src/wbso/pipeline_steps.py) - `step_assign_commits_to_sessions` implementation
- [src/wbso/pipeline.py](src/wbso/pipeline.py) - Pipeline integration
- [src/wbso/calendar_event.py](src/wbso/calendar_event.py) - WBSOSession data model with commit_messages field
