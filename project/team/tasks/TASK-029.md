# TASK-029: Unified Datetime Handling System

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Create a unified datetime handling system to standardize timestamp processing across the project. This addresses the current fragmentation of datetime parsing functions and establishes a consistent format for time-based analysis.

## Business Context

Time is the horizontal axis for project analysis, making unified datetime handling critical for accurate insights. Current implementation has multiple `parse_datetime_flexible()` functions scattered across different modules with inconsistent formats, leading to potential data integrity issues and analysis errors.

## Acceptance Criteria

- [ ] **Unified Datetime Class**: Create a standardized datetime class with consistent format (YYYY-MM-DD HH:mm:ss)
- [ ] **Smart Parsing System**: Implement intelligent parsing for multiple input formats from different data sources
- [ ] **Timezone Handling**: Standardize to local user timestamp without timezone complexity
- [ ] **Sortable Format**: Ensure datetime strings are naturally sortable in lexicographic order
- [ ] **Integration Points**: Replace existing `parse_datetime_flexible()` functions across the codebase
- [ ] **Error Handling**: Robust error handling for malformed datetime strings
- [ ] **Performance**: Efficient parsing suitable for large datasets

## Technical Requirements

### Standardized Format

- **Primary Format**: `YYYY-MM-DD HH:mm:ss` (24-hour clock, seconds accuracy)
- **Sortable**: Natural lexicographic sorting without special handling
- **No Timezones**: Local user timestamp only
- **Consistent**: Same format for all datetime operations

### Input Format Support

The system must handle these existing formats found in the codebase:

```python
# Current formats to support:
"%m/%d/%Y %I:%M:%S %p"  # 5/9/2025 8:08:14 PM
"%Y/%m/%d %H:%M:%S"     # 2025/06/24 07:30:54
"%Y-%m-%d %H:%M:%S"     # 2025-06-24 07:30:54
"%Y-%m-%dT%H:%M:%S"     # 2025-06-24T07:30:54
"%Y-%m-%dT%H:%M:%S%z"   # 2025-06-24T07:30:54+02:00
```

### Datetime Class Design

```python
class UnifiedDateTime:
    """Unified datetime handling for project time-based analysis.

    Provides consistent datetime operations with standardized format
    and smart parsing capabilities for multiple data sources.
    """

    def __init__(self, datetime_input: Union[str, datetime, None] = None):
        """Initialize with flexible input types."""

    def to_standard_format(self) -> str:
        """Return datetime in standard YYYY-MM-DD HH:mm:ss format."""

    def to_datetime(self) -> datetime:
        """Return Python datetime object."""

    @classmethod
    def parse_flexible(cls, dt_str: str) -> 'UnifiedDateTime':
        """Parse datetime string with multiple format support."""

    def is_valid(self) -> bool:
        """Check if datetime is valid and parseable."""
```

## Implementation Steps

1. **Core Datetime Class Development**

   - Create `UnifiedDateTime` class in `src/backend/datetime_utils.py`
   - Implement standardized format conversion
   - Add smart parsing for multiple input formats

2. **Integration with Existing Code**

   - Replace `parse_datetime_flexible()` functions in:
     - `src/backend/session_detection.py`
     - `docs/project/hours/scripts/integrate_work_blocks_commits.py`
     - `docs/project/hours/scripts/integrate_work_sessions_commits.py`
     - `docs/project/hours/scripts/process_all_system_events.py`
     - `docs/project/hours/scripts/analyze_system_events_updated.py`

3. **Testing and Validation**

   - Create comprehensive unit tests for all supported formats
   - Test with existing data files
   - Validate sortable behavior
   - Performance testing with large datasets

4. **Documentation and Migration**
   - Document the unified datetime system
   - Create migration guide for existing code
   - Update all affected modules

## Dependencies

- Existing datetime parsing functions across the codebase
- System events and commit data files
- Python datetime and typing modules

## Definition of Done

- [ ] `UnifiedDateTime` class implemented and tested
- [ ] All existing `parse_datetime_flexible()` functions replaced
- [ ] Comprehensive unit tests with >90% coverage
- [ ] Integration tests with existing data files
- [ ] Documentation updated with usage examples
- [ ] Performance benchmarks documented
- [ ] Code reviewed and committed

## Estimated Effort

- **Core Class Development**: 4 hours
- **Integration and Replacement**: 3 hours
- **Testing and Validation**: 2 hours
- **Documentation**: 1 hour
- **Total**: 10 hours

## Related Files

- [src/backend/session_detection.py](src/backend/session_detection.py) - Current datetime parsing
- [docs/project/hours/scripts/](docs/project/hours/scripts/) - Multiple scripts with datetime parsing
- [project/team/tasks/TASK-030.md](project/team/tasks/TASK-030.md) - Pandas Integration (follow-up task)

## Code Files

- [src/backend/datetime_utils.py](src/backend/datetime_utils.py) - New unified datetime system
- [tests/test_datetime_utils.py](tests/test_datetime_utils.py) - Comprehensive datetime testing

## Notes

This task establishes the foundation for consistent time-based analysis across the project. The unified datetime system will be essential for accurate work session tracking, commit correlation, and time-based insights generation.
