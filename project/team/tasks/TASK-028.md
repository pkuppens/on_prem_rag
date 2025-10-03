# TASK-028: Work Sessions and Commits Integration

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Overview

Create a comprehensive work log by combining WorkSessions from `all_system_events_processed.json` with commits from `commits_processed.json`, implementing intelligent assignment logic and WBSO eligibility promotion.

## Business Context

To enable accurate WBSO hours registration, we need to correlate system event work sessions with actual development activity (git commits). This integration will provide a complete picture of work activity and ensure WBSO compliance by identifying which work sessions contain eligible development work.

## Technical Requirements

### 0. Timestamp Format Standardization

- **Issue**: Git commits include timezone info (`2023-05-03T11:38:52+02:00`), work sessions use local format (`2025-04-27 17:22:37`)
- **Solution**: Parse both formats to datetime objects for accurate comparison
- **Implementation**: Use `datetime.fromisoformat()` for commits, `datetime.strptime()` for work sessions

### 1. Date Filtering

- **Filter commits**: Only process commits from 2025-05-01 onwards
- **Rationale**: Focus on recent work activity for WBSO compliance
- **Implementation**: Parse commit timestamps and filter by date >= 2025-05-01

### 2. Commit Assignment Logic

- **Assignment Rule**: Assign commits to work sessions if commit timestamp falls within session time range
- **Multiple Commits**: Allow multiple commits per work session
- **Time Range**: `commit_timestamp >= session_start_time AND commit_timestamp <= session_end_time`
- **Edge Cases**: Handle commits exactly at session boundaries

### 3. WBSO Eligibility Promotion

- **Promotion Rule**: Set `is_wbso = True` on work session if ANY assigned commit has `is_wbso = true`
- **Business Logic**: If work session contains WBSO-eligible commits, entire session becomes WBSO-eligible
- **Implementation**: Check all assigned commits for WBSO eligibility and promote session accordingly

### 4. Unassigned Commits Tracking

- **Tracking**: List all commits that don't match any work session
- **Grouping**: Group unassigned commits by date for easy review
- **Output**: Include unassigned commits summary in work_log.json
- **Format**: `{"date": "YYYY-MM-DD", "commits": [commit_objects], "count": N}`

## Implementation Plan

### Phase 1: Data Loading and Preprocessing

1. Load `all_system_events_processed.json` and extract work sessions
2. Load `commits_processed.json` and filter commits >= 2025-05-01
3. Standardize timestamp formats for both datasets
4. Create datetime objects for accurate time comparisons

### Phase 2: Assignment Algorithm

1. For each work session:
   - Find all commits within session time range
   - Assign commits to session
   - Check if any assigned commit is WBSO-eligible
   - Set `is_wbso = True` if any WBSO-eligible commit found
2. Track unassigned commits separately

### Phase 3: Output Generation

1. Create enhanced work sessions with commit assignments
2. Generate unassigned commits summary by date
3. Calculate summary statistics:
   - Total work sessions
   - WBSO-eligible work sessions
   - Total work hours (WBSO and non-WBSO)
   - Assignment rates
   - Unassigned commits count

## Expected Output Structure

```json
{
  "work_sessions": [
    {
      "session_id": "session_001",
      "start_time": "2025-04-27 17:22:37",
      "end_time": "2025-04-27 18:28:08",
      "work_hours": 1.08,
      "is_wbso": true,
      "assigned_commits": [
        {
          "timestamp": "2025-04-27T17:45:00+02:00",
          "repo_name": "on_prem_rag",
          "message": "Fix authentication bug",
          "hash": "abc123...",
          "is_wbso": true
        }
      ],
      "commit_count": 1
    }
  ],
  "unassigned_commits": {
    "2025-05-15": {
      "count": 3,
      "commits": [...]
    }
  },
  "summary": {
    "total_work_sessions": 192,
    "wbso_eligible_sessions": 45,
    "total_work_hours": 678.75,
    "wbso_work_hours": 234.50,
    "total_commits_processed": 150,
    "assigned_commits": 120,
    "unassigned_commits": 30,
    "assignment_rate": 80.0
  }
}
```

## Acceptance Criteria

- [x] All commits from 2025-05-01+ are processed and filtered correctly
- [x] Commits are correctly assigned to work sessions based on time range matching
- [x] Work sessions are promoted to WBSO-eligible when containing WBSO commits
- [x] Unassigned commits are grouped by date for manual review
- [x] Comprehensive work_log.json is generated with all required data
- [x] Summary statistics provide clear overview of work activity
- [x] Timestamp format differences are handled correctly
- [x] Multiple commits per work session are supported
- [x] Edge cases at session boundaries are handled properly

## Technical Specifications

### Input Files

- `docs/project/hours/data/all_system_events_processed.json` - Work sessions from system events
- `docs/project/hours/data/commits_processed.json` - Git commits with WBSO eligibility

### Output Files

- `docs/project/hours/data/work_log.json` - Final integrated work log
- `docs/project/hours/scripts/integrate_work_sessions_commits.py` - Integration script

### Dependencies

- Python datetime handling for timezone-aware comparisons
- JSON processing for data loading and output generation
- Logging for processing status and error handling

## Testing Requirements

### Unit Tests

- [x] Timestamp parsing for both commit and work session formats
- [x] Date filtering logic for commits >= 2025-05-01
- [x] Time range matching algorithm
- [x] WBSO eligibility promotion logic
- [x] Unassigned commits grouping by date

### Integration Tests

- [x] End-to-end processing with sample data
- [x] Output format validation
- [x] Summary statistics accuracy
- [x] Edge case handling (boundary conditions)

## Definition of Done

- [x] Integration script created and tested
- [x] All acceptance criteria met
- [x] Unit tests written and passing
- [x] Integration tests passing
- [x] Documentation updated
- [x] Code reviewed and approved
- [x] Work log generated successfully
- [x] Unassigned commits report created for manual review

## Risk Assessment

### High Risk

- **Timestamp format complexity**: Multiple timezone formats may cause parsing errors
- **Mitigation**: Comprehensive testing with various timestamp formats

### Medium Risk

- **Performance**: Large datasets may cause memory issues
- **Mitigation**: Process data in chunks if necessary

### Low Risk

- **Data quality**: Missing or malformed timestamps
- **Mitigation**: Robust error handling and logging

## Related Tasks

- TASK-025: System Events Work Block Analysis
- TASK-027: Git Commit Processing and WBSO Filtering

## Notes

This task builds upon the work completed in TASK-025 (system event processing) and TASK-027 (commit processing) to create a unified work tracking system for WBSO compliance.

## Implementation Summary

### ✅ Completed Implementation

**Integration Script**: `docs/project/hours/scripts/integrate_work_sessions_commits.py`

- Comprehensive timestamp parsing for both commit (ISO 8601 with timezone) and work session (local format) formats
- Intelligent commit assignment based on time range matching
- WBSO eligibility promotion for work sessions containing WBSO commits
- Unassigned commits grouping by date for manual review
- Complete summary statistics calculation

**Generated Work Log**: `docs/project/hours/data/work_log.json`

- **Total Work Sessions**: 192 sessions processed
- **WBSO-Eligible Sessions**: 37 sessions (19.3% of total)
- **Total Work Hours**: 678.75 hours across all sessions
- **WBSO Work Hours**: 244.77 hours (36.1% of total work hours)
- **Commits Processed**: 483 commits from 2025-05-01 onwards
- **Assignment Rate**: 39.8% (192 commits assigned to sessions)
- **Unassigned Commits**: 291 commits grouped by date for review

**Unit Tests**: `tests/test_work_sessions_commits_integration.py`

- Comprehensive test coverage for all core functionality
- Edge case testing for boundary conditions
- Error handling validation for malformed data
- Business logic validation for WBSO eligibility promotion

### Key Results

1. **Successful Integration**: Work sessions and commits are now integrated with intelligent assignment logic
2. **WBSO Compliance**: 244.77 hours of WBSO-eligible work identified and tracked
3. **Data Quality**: Robust handling of timestamp format differences and malformed data
4. **Comprehensive Reporting**: Complete work log with summary statistics for compliance reporting
5. **Manual Review Support**: Unassigned commits grouped by date for easy review and potential session creation

### Files Created/Modified

- `docs/project/hours/scripts/integrate_work_sessions_commits.py` - Main integration script
- `docs/project/hours/data/work_log.json` - Final integrated work log
- `tests/test_work_sessions_commits_integration.py` - Comprehensive unit tests
- `project/team/tasks/TASK-028.md` - Updated with completion status

The work sessions and commits integration is now complete and ready for WBSO hours registration and compliance reporting.
