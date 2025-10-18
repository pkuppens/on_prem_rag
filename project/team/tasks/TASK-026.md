# TASK-026: Integrate System Events Work Blocks with Git Commit Analysis

## Story Reference

- **Story**: STORY-008 (WBSO Hours Registration System)
- **Epic**: EPIC-002 (WBSO Compliance and Documentation)

## Task Description

Integrate system events work blocks with the existing Git commit analysis to create a comprehensive WBSO hours registration system. This task combines both data sources to provide a complete picture of work activity and improve the accuracy of hour calculations.

## Acceptance Criteria

### 1. Data Source Integration

- [ ] **Sub-criteria 1.1**: Combine system events work blocks with Git commit sessions
- [ ] **Sub-criteria 1.2**: Create mapping between work blocks and Git sessions based on time ranges
- [ ] **Sub-criteria 1.3**: Implement data structure to hold integrated session information

### 2. Conflict Resolution

- [ ] **Sub-criteria 2.1**: Handle cases where system events and Git commits show different activity patterns
- [ ] **Sub-criteria 2.2**: Implement confidence-based decision making when sources disagree
- [ ] **Sub-criteria 2.3**: Create reasoning documentation for conflict resolution decisions

### 3. Gap Analysis and Hour Calculation

- [ ] **Sub-criteria 3.1**: Identify periods of uncommitted work activity using system events
- [ ] **Sub-criteria 3.2**: Improve hour allocation by considering both data sources
- [ ] **Sub-criteria 3.3**: Ensure final hours don't exceed system session duration

### 4. Validation and Pipeline Updates

- [ ] **Sub-criteria 4.1**: Create validation rules to ensure consistency between data sources
- [ ] **Sub-criteria 4.2**: Modify existing `process_commits.py` to include system events data
- [ ] **Sub-criteria 4.3**: Ensure backward compatibility with existing outputs

## Technical Requirements

### Input Data

- System events work blocks (from TASK-025)
- Git commit analysis results (existing `process_commits.py` output)
- System events CSV files for validation

### Output Format

```json
{
  "integrated_sessions": [
    {
      "session_id": "session_001",
      "start_time": "2025-05-03 08:00:00",
      "end_time": "2025-05-03 17:30:00",
      "duration_hours": 9.5,
      "data_sources": {
        "git_commits": {
          "commit_count": 5,
          "total_hours": 6.0,
          "confidence": 0.9
        },
        "system_events": {
          "work_block_id": "wb_001",
          "system_hours": 9.5,
          "confidence": 0.95
        }
      },
      "final_hours": 8.5,
      "reasoning": "System events show longer session, Git commits show focused work"
    }
  ]
}
```

### Integration Rules

1. **Primary Source**: Use system events for session boundaries when available
2. **Secondary Source**: Use Git commits for activity details and hour allocation
3. **Conflict Resolution**: When sources disagree, use higher confidence score
4. **Gap Filling**: Use system events to identify uncommitted work periods
5. **Validation**: Ensure final hours don't exceed system session duration

## Implementation Steps

1. **Data Structure Design**

   - Define integrated session data structure
   - Create mapping between work blocks and Git sessions
   - Design conflict resolution logic

2. **Integration Algorithm Development**

   - Create logic to match system events with Git commits
   - Implement confidence-based decision making
   - Handle edge cases and data gaps

3. **Script Enhancement**

   - Create new integration script that combines system events work blocks with processed commit JSON data
   - Add system events processing pipeline
   - Implement integrated output generation

4. **Validation and Testing**
   - Test integration with existing data
   - Validate hour calculations against known patterns
   - Ensure backward compatibility with existing outputs

## Implementation Details

### Architecture Decisions

- **Script Location**: `docs/project/hours/scripts/integrate_system_events_commits.py` - New integration script that combines outputs from TASK-025 and TASK-027
- **Data Model Impact**: Enhanced `integrated_session` data structure with fields: session_id, start_time, end_time, duration_hours, data_sources (git_commits, system_events), final_hours, reasoning
- **Integration Points**: Uses work blocks from TASK-025 and processed commits from TASK-027, outputs integrated sessions for downstream processing

### Tool and Dependency Specifications

- **Tool Versions**: Python>=3.12, pandas>=2.0.0 for data processing
- **Configuration**: Integration rules defined in script constants (primary source, conflict resolution logic)
- **Documentation**: Add integration rules to `docs/project/hours/data/INTEGRATION_RULES.md`

### Example Implementation

```python
def integrate_data_sources(work_blocks, git_sessions):
    """Integrate system events work blocks with Git commit sessions.

    Integration rules:
    1. Primary source: System events for session boundaries
    2. Secondary source: Git commits for activity details
    3. Conflict resolution: Use higher confidence score
    4. Gap filling: Use system events for uncommitted work periods
    """
    integrated_sessions = []
    # Implementation details...
    return integrated_sessions
```

## Dependencies

- TASK-025 (System Events Work Block Analysis) completed
- TASK-027 (CSV Commit Data Processing to JSON Format) completed
- System events CSV files and work block analysis results
- Processed commit JSON data from TASK-027

## Definition of Done

- [ ] Integration script completed and tested
- [ ] Sample integrated sessions generated from existing data
- [ ] Documentation of integration rules and conflict resolution
- [ ] Updated processing pipeline that includes system events
- [ ] Validation tests pass with both data sources
- [ ] Code reviewed and committed to repository

## Estimated Effort

- **Design and Planning**: 2 hours
- **Integration Development**: 4 hours
- **Testing and Validation**: 2 hours
- **Documentation**: 1 hour
- **Total**: 9 hours

## Notes

This task creates the foundation for a comprehensive WBSO hours registration system that leverages both Git commit data and system activity data. The integration provides better accuracy and captures work activity that might not be reflected in Git commits alone.

## Related Files

- [docs/project/hours/process_commits.py](docs/project/hours/process_commits.py) - Legacy commit processing script
- [docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md](docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md)
- [project/team/tasks/TASK-025.md](project/team/tasks/TASK-025.md) - System Events Work Block Analysis
- [project/team/tasks/TASK-027.md](project/team/tasks/TASK-027.md) - CSV Commit Data Processing to JSON Format
