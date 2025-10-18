# TASK-030: Pandas Integration for Time-Based Data Analysis

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Integrate pandas for advanced time-based data analysis and visualization. This task adds pandas as a dependency and creates the foundation for sophisticated time series analysis, data aggregation, and insights generation.

## Business Context

Pandas provides powerful time series capabilities essential for analyzing work patterns, commit frequencies, and time-based insights. The current CSV-based processing is limited; pandas will enable advanced analytics like time range filtering, aggregation by periods, and statistical analysis of work patterns.

## Acceptance Criteria

- [x] **Pandas Dependency**: Add pandas to project dependencies using `uv add`
- [x] **Data Loading Utilities**: Create utilities to load system events and commit data into pandas DataFrames
- [x] **Time Series Indexing**: Implement proper datetime indexing for time-based operations
- [x] **Data Aggregation**: Create functions for time-based aggregation (hourly, daily, weekly, monthly)
- [x] **Time Range Filtering**: Implement efficient filtering by time ranges
- [x] **Integration with UnifiedDateTime**: Ensure compatibility with TASK-029 datetime system
- [x] **Performance Optimization**: Optimize for large datasets with appropriate data types

## Technical Requirements

### Pandas Integration

```python
# Example DataFrame structure for system events
system_events_df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2025-05-03 08:00:00', '2025-05-03 17:30:00']),
    'event_type': ['startup', 'shutdown'],
    'event_id': [6005, 1074],
    'computer_name': ['WORKSTATION-01', 'WORKSTATION-01']
})

# Example DataFrame structure for commits
commits_df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2025-05-03 10:30:00', '2025-05-03 14:15:00']),
    'repo_name': ['on_prem_rag', 'on_prem_rag'],
    'author': ['Pieter Kuppens', 'Pieter Kuppens'],
    'message': ['Fix authentication bug', 'Add new feature'],
    'is_wbso': [True, True]
})
```

### Time-Based Operations

```python
class TimeSeriesAnalyzer:
    """Pandas-based time series analysis for work session data."""

    def __init__(self, system_events_df: pd.DataFrame, commits_df: pd.DataFrame):
        """Initialize with system events and commits data."""

    def filter_by_time_range(self, start_time: str, end_time: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Filter data by time range for zoom operations."""

    def aggregate_by_period(self, period: str) -> pd.DataFrame:
        """Aggregate data by hour/day/week/month."""

    def detect_work_sessions(self) -> pd.DataFrame:
        """Detect work sessions using pandas operations."""

    def correlate_commits_with_sessions(self) -> pd.DataFrame:
        """Correlate commits with work sessions."""
```

### Data Loading Utilities

```python
def load_system_events_data(data_dir: Path) -> pd.DataFrame:
    """Load and combine all system events CSV files into a single DataFrame."""

def load_commits_data(commits_file: Path) -> pd.DataFrame:
    """Load processed commits JSON into a pandas DataFrame."""

def prepare_time_series_data(system_events_df: pd.DataFrame, commits_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare data for time series analysis with proper datetime indexing."""
```

## Implementation Steps

1. **Dependency Management**

   - Add pandas to `pyproject.toml` using `uv add pandas`
   - Add related packages: `uv add --dev jupyter matplotlib seaborn`
   - Update environment setup documentation

2. **Data Loading Infrastructure**

   - Create `src/backend/data_analysis/` directory
   - Implement data loading utilities for CSV and JSON files
   - Add data validation and type conversion

3. **Time Series Analysis Framework**

   - Create `TimeSeriesAnalyzer` class
   - Implement time range filtering and aggregation
   - Add work session detection using pandas operations

4. **Integration with Existing Data**

   - Update existing scripts to use pandas DataFrames
   - Ensure compatibility with unified datetime system
   - Add performance optimizations for large datasets

5. **Testing and Validation**
   - Create unit tests for pandas operations
   - Test with existing data files
   - Validate time series operations
   - Performance testing with large datasets

## Dependencies

- TASK-029 (Unified Datetime Handling System)
- Existing system events and commit data files
- Python pandas library
- Jupyter notebook environment

## Definition of Done

- [x] Pandas added to project dependencies
- [x] Data loading utilities implemented and tested
- [x] Time series analysis framework created
- [x] Integration with existing data sources completed
- [x] Unit tests with >90% coverage
- [x] Performance benchmarks documented
- [x] Documentation updated with usage examples
- [x] Code reviewed and committed

## Estimated Effort

- **Dependency Setup**: 1 hour
- **Data Loading Infrastructure**: 3 hours
- **Time Series Framework**: 4 hours
- **Integration and Testing**: 3 hours
- **Documentation**: 1 hour
- **Total**: 12 hours

## Related Files

- [project/team/tasks/TASK-029.md](project/team/tasks/TASK-029.md) - Unified Datetime System (prerequisite)
- [project/team/tasks/TASK-031.md](project/team/tasks/TASK-031.md) - Jupyter Visualization (follow-up task)
- [docs/project/hours/data/](docs/project/hours/data/) - Source data files
- [pyproject.toml](pyproject.toml) - Dependencies configuration

## Code Files

- [src/backend/data_analysis/](src/backend/data_analysis/) - New pandas-based analysis module
- [src/backend/data_analysis/data_loader.py](src/backend/data_analysis/data_loader.py) - Data loading utilities
- [src/backend/data_analysis/time_series_analyzer.py](src/backend/data_analysis/time_series_analyzer.py) - Time series analysis framework
- [tests/test_data_analysis.py](tests/test_data_analysis.py) - Pandas integration tests

## Notes

This task creates the foundation for advanced time-based analytics. Pandas integration will enable sophisticated analysis of work patterns, commit correlations, and time-based insights that are essential for accurate WBSO hours registration and project insights.
