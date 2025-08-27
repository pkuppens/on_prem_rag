# TASK-026: Integrate System Events Work Blocks with Git Commit Analysis

## Story Reference

- **Story**: STORY-008 (WBSO Hours Registration System)
- **Epic**: EPIC-002 (WBSO Compliance and Documentation)

## Task Description

Integrate system events work blocks with the existing Git commit analysis to create a comprehensive WBSO hours registration system. This task combines both data sources to provide a complete picture of work activity and improve the accuracy of hour calculations.

## Acceptance Criteria

- [ ] **Data Source Integration**: Combine system events work blocks with Git commit sessions
- [ ] **Conflict Resolution**: Handle cases where system events and Git commits show different activity patterns
- [ ] **Gap Analysis**: Identify periods of uncommitted work activity using system events
- [ ] **Enhanced Hour Calculation**: Improve hour allocation by considering both data sources
- [ ] **Validation Logic**: Create validation rules to ensure consistency between data sources
- [ ] **Updated Processing Pipeline**: Modify existing `process_commits.py` to include system events data

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

   - Modify `process_commits.py` to accept system events input
   - Add system events processing pipeline
   - Implement integrated output generation

4. **Validation and Testing**
   - Test integration with existing data
   - Validate hour calculations against known patterns
   - Ensure backward compatibility with existing outputs

## Dependencies

- TASK-025 (System Events Work Block Analysis) completed
- Existing `process_commits.py` script
- System events CSV files and work block analysis results

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

- [docs/project/hours/process_commits.py](docs/project/hours/process_commits.py)
- [docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md](docs/project/hours/data/SYSTEM_EVENTS_FORMAT.md)
- [project/team/tasks/TASK-025.md](project/team/tasks/TASK-025.md) - System Events Work Block Analysis
