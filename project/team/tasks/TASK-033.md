# TASK-033: Time Range Operations and Zoom Capabilities

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Implement time range operations and zoom capabilities for analyzing work patterns at different time granularities. This enables users to zoom into specific time ranges (hours, days, weeks, months) and perform analysis at the appropriate level of detail.

## Business Context

Time-based analysis requires the ability to zoom into different time ranges to understand patterns at various granularities. Users need to analyze work sessions at hourly detail, daily patterns, weekly trends, and monthly summaries for comprehensive insights and WBSO compliance reporting.

## Acceptance Criteria

- [ ] **Time Range Class**: Create a robust time range class for representing and manipulating time intervals
- [ ] **Zoom Operations**: Implement zoom functionality for hours, days, weeks, and months
- [ ] **Range Filtering**: Efficient filtering of data by time ranges
- [ ] **Aggregation by Period**: Aggregate data by different time periods
- [ ] **Range Validation**: Validate time ranges and handle edge cases
- [ ] **Performance Optimization**: Efficient operations for large datasets
- [ ] **Integration with Visualization**: Seamless integration with Jupyter visualization tools

## Technical Requirements

### Time Range Class Design

```python
class TimeRange:
    """Represents a time range with zoom and aggregation capabilities."""

    def __init__(self, start_time: Union[str, datetime], end_time: Union[str, datetime]):
        """Initialize time range with start and end times."""

    def duration(self) -> timedelta:
        """Get the duration of the time range."""

    def contains(self, timestamp: Union[str, datetime]) -> bool:
        """Check if timestamp falls within the time range."""

    def zoom_to_hours(self) -> List['TimeRange']:
        """Split time range into hourly chunks."""

    def zoom_to_days(self) -> List['TimeRange']:
        """Split time range into daily chunks."""

    def zoom_to_weeks(self) -> List['TimeRange']:
        """Split time range into weekly chunks."""

    def zoom_to_months(self) -> List['TimeRange']:
        """Split time range into monthly chunks."""

    def expand_by(self, duration: timedelta) -> 'TimeRange':
        """Expand time range by specified duration."""

    def contract_by(self, duration: timedelta) -> 'TimeRange':
        """Contract time range by specified duration."""
```

### Zoom Operations

```python
class TimeRangeZoomer:
    """Handles zoom operations for time-based analysis."""

    def __init__(self, data: pd.DataFrame):
        """Initialize with pandas DataFrame."""
        self.data = data
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data = self.data.set_index('timestamp')

    def zoom_to_period(self, time_range: TimeRange, period: str) -> pd.DataFrame:
        """Zoom data to specific time period granularity."""
        filtered_data = self.data[time_range.start_time:time_range.end_time]

        if period == 'hour':
            return filtered_data.resample('H').agg(self._get_aggregation_rules())
        elif period == 'day':
            return filtered_data.resample('D').agg(self._get_aggregation_rules())
        elif period == 'week':
            return filtered_data.resample('W').agg(self._get_aggregation_rules())
        elif period == 'month':
            return filtered_data.resample('M').agg(self._get_aggregation_rules())
        else:
            raise ValueError(f"Unsupported period: {period}")

    def get_time_range_summary(self, time_range: TimeRange) -> Dict[str, Any]:
        """Get summary statistics for a time range."""
        filtered_data = self.data[time_range.start_time:time_range.end_time]

        return {
            'start_time': time_range.start_time,
            'end_time': time_range.end_time,
            'duration_hours': time_range.duration().total_seconds() / 3600,
            'total_events': len(filtered_data),
            'work_sessions': self._count_work_sessions(filtered_data),
            'commits': self._count_commits(filtered_data),
            'activity_score': self._calculate_activity_score(filtered_data)
        }
```

### Time Range Operations

```python
class TimeRangeOperations:
    """Advanced operations for time range analysis."""

    def __init__(self, system_events_df: pd.DataFrame, commits_df: pd.DataFrame):
        """Initialize with system events and commits data."""
        self.system_events = system_events_df
        self.commits = commits_df

    def find_work_sessions_in_range(self, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Find work sessions within the specified time range."""
        filtered_events = self.system_events[
            (self.system_events['timestamp'] >= time_range.start_time) &
            (self.system_events['timestamp'] <= time_range.end_time)
        ]

        return self._detect_work_sessions(filtered_events)

    def find_commits_in_range(self, time_range: TimeRange) -> pd.DataFrame:
        """Find commits within the specified time range."""
        return self.commits[
            (self.commits['timestamp'] >= time_range.start_time) &
            (self.commits['timestamp'] <= time_range.end_time)
        ]

    def correlate_activity_in_range(self, time_range: TimeRange) -> Dict[str, Any]:
        """Correlate work sessions and commits within time range."""
        work_sessions = self.find_work_sessions_in_range(time_range)
        commits = self.find_commits_in_range(time_range)

        return {
            'work_sessions': work_sessions,
            'commits': commits,
            'correlation_score': self._calculate_correlation_score(work_sessions, commits),
            'time_range': time_range
        }

    def get_activity_timeline(self, time_range: TimeRange, granularity: str = 'hour') -> pd.DataFrame:
        """Get activity timeline for the time range."""
        # Implementation for creating activity timeline
        pass
```

## Implementation Steps

1. **Core Time Range Class**

   - Create `TimeRange` class with basic operations
   - Implement zoom functionality for different periods
   - Add validation and error handling

2. **Zoom Operations Framework**

   - Create `TimeRangeZoomer` class
   - Implement period-based aggregation
   - Add performance optimizations for large datasets

3. **Advanced Operations**

   - Create `TimeRangeOperations` class
   - Implement work session and commit correlation
   - Add activity timeline generation

4. **Integration with Existing Systems**

   - Integrate with unified datetime system
   - Connect with pandas data analysis framework
   - Ensure compatibility with visualization tools

5. **Testing and Validation**
   - Create comprehensive test suite
   - Test with real data from different time ranges
   - Validate performance with large datasets

## Dependencies

- TASK-029 (Unified Datetime Handling System)
- TASK-030 (Pandas Integration for Time-Based Data Analysis)
- Existing system events and commit data
- Python datetime and pandas modules

## Definition of Done

- [ ] Time range class implemented with all required operations
- [ ] Zoom functionality working for all time periods
- [ ] Time range operations framework completed
- [ ] Integration with existing systems completed
- [ ] Comprehensive test suite with >90% coverage
- [ ] Performance optimized for large datasets
- [ ] Documentation updated with usage examples
- [ ] Code reviewed and committed

## Estimated Effort

- **Core Time Range Class**: 3 hours
- **Zoom Operations Framework**: 4 hours
- **Advanced Operations**: 4 hours
- **Integration**: 2 hours
- **Testing and Validation**: 3 hours
- **Documentation**: 1 hour
- **Total**: 17 hours

## Related Files

- [project/team/tasks/TASK-029.md](project/team/tasks/TASK-029.md) - Unified Datetime System
- [project/team/tasks/TASK-030.md](project/team/tasks/TASK-030.md) - Pandas Integration
- [project/team/tasks/TASK-031.md](project/team/tasks/TASK-031.md) - Jupyter Visualization

## Code Files

- [src/backend/data_analysis/time_range.py](src/backend/data_analysis/time_range.py) - Time range class
- [src/backend/data_analysis/zoom_operations.py](src/backend/data_analysis/zoom_operations.py) - Zoom operations
- [src/backend/data_analysis/time_range_operations.py](src/backend/data_analysis/time_range_operations.py) - Advanced operations
- [tests/test_time_range_operations.py](tests/test_time_range_operations.py) - Time range testing

## Notes

This task completes the time-based analysis infrastructure by providing sophisticated time range operations and zoom capabilities. These features are essential for detailed analysis of work patterns and comprehensive WBSO compliance reporting.
