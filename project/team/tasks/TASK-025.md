# TASK-025: System Events Work Block Analysis

## Story Reference

- **Story**: STORY-008 (WBSO Hours Registration System)
- **Epic**: EPIC-002 (WBSO Compliance and Documentation)

## Task Description

Analyze system events data to define work blocks that can supplement Git commit data for WBSO hours registration. This task focuses on processing the existing system events CSV files to identify work session boundaries and activity patterns.

## Acceptance Criteria

### 1. Work Block Definition

- [x] **Sub-criteria 1.1**: Define clear criteria for what constitutes a work block from system events
- [x] **Sub-criteria 1.2**: Create logic to detect work session start/end times from system events
- [x] **Sub-criteria 1.3**: Implement confidence scoring based on event completeness and timing

### 2. Event Pattern Analysis

- [x] **Sub-criteria 2.1**: Identify patterns in system startup/shutdown events that indicate work sessions
- [x] **Sub-criteria 2.2**: Map event sequences to work sessions with proper time boundaries
- [x] **Sub-criteria 2.3**: Handle edge cases (unexpected shutdowns, missing events)

### 3. Data Processing Implementation

- [x] **Sub-criteria 3.1**: Develop Python script to process system events CSV files into work blocks
- [x] **Sub-criteria 3.2**: Generate structured output with work block definitions (start time, end time, duration, confidence score)
- [x] **Sub-criteria 3.3**: Implement error handling for malformed CSV data

### 4. Integration Planning

- [x] **Sub-criteria 4.1**: Document how work blocks will integrate with existing Git commit analysis
- [x] **Sub-criteria 4.2**: Define output format compatible with downstream processing
- [x] **Sub-criteria 4.3**: Create validation rules for work block data quality

## Technical Requirements

### Input Data

- System events CSV files: `system_events_20250826.csv`, `system_events_20250821.csv`
- Event types: System startup (6005), shutdown (1074, 6006), sleep (42), unexpected shutdown (41, 6008)
- Time range: May-August 2025

### Output Format

```json
{
  "work_blocks": [
    {
      "block_id": "wb_001",
      "start_time": "2025-05-03 08:00:00",
      "end_time": "2025-05-03 17:30:00",
      "duration_hours": 9.5,
      "confidence_score": 0.95,
      "evidence": ["startup_event", "shutdown_event"],
      "session_type": "full_day"
    }
  ]
}
```

### Work Block Rules

1. **Start Detection**: System startup (EventId 6005) during work hours (8:00-18:00)
2. **End Detection**: System shutdown (EventId 1074) or sleep (EventId 42)
3. **Minimum Duration**: 30 minutes to qualify as work block
4. **Maximum Duration**: 12 hours (with breaks for longer sessions)
5. **Confidence Scoring**: Based on event completeness and timing

## Implementation Steps

1. **Data Analysis Phase**

   - Parse system events CSV files
   - Identify event patterns and frequencies
   - Map event sequences to work sessions

2. **Algorithm Development**

   - Create work block detection logic
   - Implement confidence scoring
   - Handle edge cases (unexpected shutdowns, missing events)

3. **Script Development**

   - Create `analyze_system_events.py` script
   - Implement CSV parsing and event processing
   - Generate work block JSON output

4. **Validation and Testing**
   - Test with existing system events data
   - Validate work block definitions against known patterns
   - Compare with Git commit timestamps for correlation

## Implementation Details

### Architecture Decisions

- **Script Location**: `docs/project/hours/scripts/analyze_system_events.py` - Located in hours processing scripts directory for logical grouping
- **Data Model Impact**: New `work_block` data structure with fields: block_id, start_time, end_time, duration_hours, confidence_score, evidence, session_type
- **Integration Points**: Output format designed to integrate with existing Git commit analysis in TASK-026

### Tool and Dependency Specifications

- **Tool Versions**: Python>=3.12, pandas>=2.0.0 for CSV processing
- **Configuration**: No external configuration required - uses hardcoded event type mappings
- **Documentation**: Add work block detection rules to `docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md`

### Example Implementation

```python
def detect_work_blocks(events_df):
    """Detect work blocks from system events data.

    Work block rules:
    1. Start: System startup (EventId 6005) during work hours (8:00-18:00)
    2. End: System shutdown (EventId 1074) or sleep (EventId 42)
    3. Minimum duration: 30 minutes
    4. Maximum duration: 12 hours
    """
    work_blocks = []
    # Implementation details...
    return work_blocks
```

## Dependencies

- Existing system events CSV files in `docs/project/hours/data/`
- Python environment with pandas/csv processing libraries
- Understanding of WBSO hours registration requirements

## Definition of Done

- [x] Work block analysis script completed and tested
- [x] Sample work blocks generated from existing system events data
- [x] Documentation of work block detection rules and confidence scoring
- [x] Integration plan documented for combining with Git commit analysis
- [x] Code reviewed and committed to repository

## Estimated Effort

- **Analysis**: 2 hours
- **Script Development**: 3 hours
- **Testing and Validation**: 1 hour
- **Documentation**: 1 hour
- **Total**: 7 hours

## Notes

This task builds on the system events format documentation created in TASK-024 and provides the foundation for integrating system activity data with Git commit analysis for comprehensive WBSO hours registration.

## Related Files

- [docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md](docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md)
- [docs/project/hours/data/system_events_20250826.csv](docs/project/hours/data/system_events_20250826.csv)
- [docs/project/hours/process_commits.py](docs/project/hours/process_commits.py)
