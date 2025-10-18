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

### 1. Unified Datetime Class

- [x] **Sub-criteria 1.1**: Create a standardized datetime class with consistent format (YYYY-MM-DD HH:mm:ss)
- [x] **Sub-criteria 1.2**: Implement flexible input types (string, datetime, None) with proper initialization
- [x] **Sub-criteria 1.3**: Ensure datetime strings are naturally sortable in lexicographic order

### 2. Smart Parsing System

- [x] **Sub-criteria 2.1**: Implement intelligent parsing for multiple input formats from different data sources
- [x] **Sub-criteria 2.2**: Support all existing formats found in the codebase (system events, git commits, CSV files)
- [x] **Sub-criteria 2.3**: Standardize to local user timestamp without timezone complexity

### 3. Integration and Performance

- [x] **Sub-criteria 3.1**: Replace existing `parse_datetime_flexible()` functions across the codebase
- [x] **Sub-criteria 3.2**: Implement robust error handling for malformed datetime strings
- [x] **Sub-criteria 3.3**: Ensure efficient parsing suitable for large datasets

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

## Implementation Details

### Architecture Decisions

- **Script Location**: `src/backend/datetime_utils.py` - Core utility module for datetime operations
- **Data Model Impact**: New `UnifiedDateTime` class that standardizes all datetime operations across the project
- **Integration Points**: Replaces scattered `parse_datetime_flexible()` functions in session_detection.py and hours processing scripts

### Tool and Dependency Specifications

- **Tool Versions**: Python>=3.12, datetime module (built-in), typing module (built-in)
- **Configuration**: No external configuration required - uses hardcoded format patterns
- **Documentation**: Add unified datetime system documentation to `docs/technical/DATETIME_SYSTEM.md`

### Example Implementation

```python
class UnifiedDateTime:
    """Unified datetime handling for project time-based analysis.

    Provides consistent datetime operations with standardized format
    and smart parsing capabilities for multiple data sources.
    """

    def __init__(self, datetime_input: Union[str, datetime, None] = None):
        """Initialize with flexible input types."""
        # Implementation details...

    @classmethod
    def parse_flexible(cls, dt_str: str) -> 'UnifiedDateTime':
        """Parse datetime string with multiple format support."""
        # Implementation details...
```

## Dependencies

- Existing datetime parsing functions across the codebase
- System events and commit data files
- Python datetime and typing modules

## Definition of Done

- [x] `UnifiedDateTime` class implemented and tested
- [x] All existing `parse_datetime_flexible()` functions replaced
- [x] Comprehensive unit tests with >90% coverage
- [x] Integration tests with existing data files
- [x] Documentation updated with usage examples
- [x] Performance benchmarks documented
- [x] Code reviewed and committed

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

- [src/backend/datetime_utils.py](src/backend/datetime_utils.py) - Unified datetime system implementation with UnifiedDateTime class
- [tests/test_datetime_utils.py](tests/test_datetime_utils.py) - Comprehensive test suite with 24 test cases covering all functionality
- [src/backend/session_detection.py](src/backend/session_detection.py) - Updated to use unified datetime system
- [docs/project/hours/scripts/integrate_work_blocks_commits.py](docs/project/hours/scripts/integrate_work_blocks_commits.py) - Updated to use unified datetime system
- [docs/project/hours/scripts/process_all_system_events.py](docs/project/hours/scripts/process_all_system_events.py) - Updated to use unified datetime system
- [docs/technical/DATETIME_SYSTEM.md](docs/technical/DATETIME_SYSTEM.md) - Comprehensive documentation and migration guide

## Notes

This task establishes the foundation for consistent time-based analysis across the project. The unified datetime system will be essential for accurate work session tracking, commit correlation, and time-based insights generation.
