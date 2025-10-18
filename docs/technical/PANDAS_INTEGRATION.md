# Pandas Integration for Time-Based Data Analysis

This document describes the pandas integration implemented in TASK-030 for advanced time-based data analysis and visualization in the WBSO hours registration system.

## Overview

The pandas integration provides powerful time series capabilities essential for analyzing work patterns, commit frequencies, and time-based insights. It replaces the limited CSV-based processing with sophisticated analytics including time range filtering, aggregation by periods, and statistical analysis of work patterns.

## Architecture

### Core Components

1. **Data Loading Utilities** (`data_loader.py`)
   - Load system events from CSV files
   - Load commit data from JSON files
   - Prepare data for time series analysis

2. **Time Series Analyzer** (`time_series_analyzer.py`)
   - Time range filtering and aggregation
   - Work session detection
   - Commit-session correlation
   - Work pattern analysis

3. **Integration with UnifiedDateTime** (TASK-029)
   - Consistent datetime parsing across all data sources
   - Standardized timestamp formatting
   - Robust error handling for malformed datetime strings

## Usage Examples

### Basic Data Loading

```python
from pathlib import Path
from backend.data_analysis import load_system_events_data, load_commits_data

# Load system events from CSV files
data_dir = Path("docs/project/hours/data/system_events")
system_events_df = load_system_events_data(data_dir)

# Load commit data from JSON file
commits_file = Path("docs/project/hours/data/commits.json")
commits_df = load_commits_data(commits_file)

print(f"Loaded {len(system_events_df)} system events and {len(commits_df)} commits")
```

### Time Series Analysis

```python
from backend.data_analysis import TimeSeriesAnalyzer, prepare_time_series_data

# Prepare data for time series analysis
prepared_system_events, prepared_commits = prepare_time_series_data(
    system_events_df, commits_df
)

# Initialize analyzer
analyzer = TimeSeriesAnalyzer(prepared_system_events, prepared_commits)

# Filter by time range
filtered_system, filtered_commits = analyzer.filter_by_time_range(
    "2025-01-15 09:00:00", 
    "2025-01-15 17:00:00"
)

# Aggregate by daily periods
daily_aggregation = analyzer.aggregate_by_period('D')
print(daily_aggregation.head())
```

### Work Session Detection

```python
# Detect work sessions from system events
sessions_df = analyzer.detect_work_sessions()

print(f"Detected {len(sessions_df)} work sessions")
print(sessions_df[['session_start', 'session_end', 'duration_minutes', 'computer_name']])

# Correlate commits with work sessions
correlated_commits = analyzer.correlate_commits_with_sessions()

# Analyze commits made during work sessions
commits_in_sessions = correlated_commits[correlated_commits['session_id'].notna()]
print(f"{len(commits_in_sessions)}/{len(correlated_commits)} commits were made during work sessions")
```

### Work Pattern Analysis

```python
# Get comprehensive work pattern summary
summary = analyzer.get_work_patterns_summary()

print("Work Pattern Summary:")
print(f"Total work sessions: {summary['work_sessions']['total_sessions']}")
print(f"Average session duration: {summary['work_sessions']['avg_duration_minutes']:.1f} minutes")
print(f"Total work hours: {summary['work_sessions']['total_work_hours']:.1f} hours")
print(f"WBSO commits: {summary['commits']['wbso_commits']}/{summary['commits']['total_commits']} ({summary['commits']['wbso_percentage']:.1f}%)")
```

### Advanced Analytics

```python
# Analyze work patterns by hour of day
hourly_analysis = analyzer.aggregate_by_period('H')

# Find peak work hours
peak_hours = hourly_analysis[hourly_analysis['system_events_count'] > 0].index.hour
print(f"Peak work hours: {sorted(peak_hours)}")

# Analyze commit patterns
commits_by_hour = analyzer.commits_df.groupby(analyzer.commits_df.index.hour).size()
print("Commits by hour:")
print(commits_by_hour.sort_values(ascending=False).head())

# Calculate productivity metrics
if 'productivity_metrics' in summary:
    metrics = summary['productivity_metrics']
    print(f"Commits per work hour: {metrics.get('commits_per_work_hour', 0):.2f}")
    print(f"Session-commit correlation: {metrics.get('session_commit_correlation', 0):.1f}%")
```

## Data Structures

### System Events DataFrame

```python
# Example structure
system_events_df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2025-01-15 08:00:00', '2025-01-15 17:30:00']),
    'event_type': ['startup', 'shutdown'],
    'event_id': [6005, 1074],
    'computer_name': ['WORKSTATION-01', 'WORKSTATION-01']
})

# Computed columns added by analyzer
system_events_df['is_startup'] = system_events_df['event_type'].str.contains('startup', case=False)
system_events_df['is_shutdown'] = system_events_df['event_type'].str.contains('shutdown', case=False)
system_events_df['hour'] = system_events_df.index.hour
system_events_df['day_of_week'] = system_events_df.index.dayofweek
system_events_df['date'] = system_events_df.index.date
```

### Commits DataFrame

```python
# Example structure
commits_df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2025-01-15 10:30:00', '2025-01-15 14:15:00']),
    'repo_name': ['on_prem_rag', 'on_prem_rag'],
    'author': ['Pieter Kuppens', 'Pieter Kuppens'],
    'message': ['Fix authentication bug', 'Add new feature'],
    'is_wbso': [True, True]
})

# Computed columns added by analyzer
commits_df['hour'] = commits_df.index.hour
commits_df['day_of_week'] = commits_df.index.dayofweek
commits_df['date'] = commits_df.index.date
commits_df['message_length'] = commits_df['message'].str.len()
```

### Work Sessions DataFrame

```python
# Example structure
sessions_df = pd.DataFrame({
    'session_start': pd.to_datetime(['2025-01-15 08:00:00', '2025-01-16 09:00:00']),
    'session_end': pd.to_datetime(['2025-01-15 17:30:00', '2025-01-16 18:00:00']),
    'duration_minutes': [570.0, 540.0],
    'computer_name': ['WORKSTATION-01', 'WORKSTATION-02']
})
```

## Performance Considerations

### Data Type Optimization

The system automatically optimizes DataFrame data types for memory efficiency:

- String columns with repeated values are converted to categories
- Integer columns are downcast to appropriate sizes (int8, int16, int32)
- Timestamps are properly indexed for fast time-based operations

### Large Dataset Handling

For large datasets, consider:

```python
# Process data in chunks for memory efficiency
chunk_size = 10000
for chunk in pd.read_csv(large_file, chunksize=chunk_size):
    # Process chunk
    processed_chunk = process_chunk(chunk)
    # Save or aggregate results
```

### Time Series Indexing

Always use datetime indexing for time-based operations:

```python
# Efficient time range filtering
filtered_data = df.loc['2025-01-15':'2025-01-16']

# Efficient resampling
daily_data = df.resample('D').sum()
```

## Error Handling

### Common Issues and Solutions

1. **Invalid DateTime Formats**
   ```python
   # The system handles various formats automatically
   # If parsing fails, check the datetime string format
   unified_dt = UnifiedDateTime("your_datetime_string")
   if not unified_dt.is_valid():
       print(f"Invalid datetime: {unified_dt}")
   ```

2. **Missing Data**
   ```python
   # Handle missing data gracefully
   if df.empty:
       print("No data available")
       return pd.DataFrame()
   ```

3. **Memory Issues with Large Datasets**
   ```python
   # Use data type optimization
   df = _optimize_dataframe_types(df)
   
   # Process in chunks
   for chunk in pd.read_csv(file, chunksize=10000):
       process_chunk(chunk)
   ```

## Integration with Existing Systems

### UnifiedDateTime Integration

The pandas integration seamlessly works with the UnifiedDateTime system from TASK-029:

```python
# Consistent datetime parsing across all data sources
from backend.datetime_utils import UnifiedDateTime

# Parse various datetime formats
dt1 = UnifiedDateTime("2025-01-15 08:00:00")  # Standard format
dt2 = UnifiedDateTime("1/15/2025 8:00:00 AM")  # US format
dt3 = UnifiedDateTime("2025-01-15T08:00:00")   # ISO format

# All produce consistent results
assert dt1.to_standard_format() == dt2.to_standard_format()
assert dt2.to_standard_format() == dt3.to_standard_format()
```

### Session Detection Integration

The system integrates with existing session detection logic:

```python
# Use existing session detection patterns
startup_events = system_events_df[system_events_df['is_startup']]
shutdown_events = system_events_df[system_events_df['is_shutdown']]

# Enhanced session detection with pandas operations
sessions = analyzer.detect_work_sessions()
```

## Testing

### Running Tests

```bash
# Run all data analysis tests
uv run pytest tests/test_data_analysis.py -v

# Run specific test class
uv run pytest tests/test_data_analysis.py::TestDataLoader -v

# Run with coverage
uv run pytest tests/test_data_analysis.py --cov=src/backend/data_analysis --cov-report=term
```

### Test Coverage

The test suite covers:

- Data loading from CSV and JSON files
- Time series analysis operations
- Work session detection
- Commit-session correlation
- Error handling scenarios
- Integration with UnifiedDateTime system

## Future Enhancements

### Planned Features

1. **Advanced Visualization**
   - Integration with matplotlib and seaborn
   - Interactive time series plots
   - Work pattern heatmaps

2. **Machine Learning Integration**
   - Anomaly detection in work patterns
   - Predictive analytics for work sessions
   - Clustering of work behaviors

3. **Real-time Analysis**
   - Streaming data processing
   - Live work session monitoring
   - Real-time productivity metrics

### Performance Improvements

1. **Parallel Processing**
   - Multi-threaded data loading
   - Parallel aggregation operations
   - Distributed processing for large datasets

2. **Caching**
   - Results caching for expensive operations
   - Incremental data processing
   - Smart cache invalidation

## Code Files

- [src/backend/data_analysis/__init__.py](src/backend/data_analysis/__init__.py) - Module initialization and exports
- [src/backend/data_analysis/data_loader.py](src/backend/data_analysis/data_loader.py) - Data loading utilities for CSV and JSON files
- [src/backend/data_analysis/time_series_analyzer.py](src/backend/data_analysis/time_series_analyzer.py) - Time series analysis framework
- [tests/test_data_analysis.py](tests/test_data_analysis.py) - Comprehensive test suite with 24 test cases
- [docs/technical/PANDAS_INTEGRATION.md](docs/technical/PANDAS_INTEGRATION.md) - This documentation file

## References

- [TASK-030: Pandas Integration for Time-Based Data Analysis](project/team/tasks/TASK-030.md)
- [TASK-029: Unified Datetime Handling System](project/team/tasks/TASK-029.md)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Time Series Analysis with Pandas](https://pandas.pydata.org/docs/user_guide/timeseries.html)
