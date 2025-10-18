# TASK-031: Jupyter Notebook Infrastructure for Time-Based Visualization

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Create Jupyter notebook infrastructure for interactive time-based data visualization and analysis. This enables zoom operations (hours, days, weeks, months) and provides interactive exploration of work patterns and commit correlations.

## Business Context

Interactive visualization is essential for understanding work patterns and validating time-based insights. Jupyter notebooks provide the ideal environment for exploratory data analysis, allowing users to zoom into specific time ranges and interactively explore correlations between system events and commits.

## Acceptance Criteria

- [x] **Jupyter Environment Setup**: Configure Jupyter notebook environment with required dependencies
- [x] **Computer Activity Timeline**: Create daily timeline plot showing computer on/off periods using system events data
- [x] **Commit Overlay Visualization**: Overlay commit markers on computer activity timeline with repo-specific styling
- [x] **Interactive Time Range Selection**: Enable zoom capabilities (hours, days, weeks, months)
- [x] **Dynamic Legend Management**: Show only active repositories in selected time range
- [x] **Export Capabilities**: Export visualizations and analysis results
- [x] **Documentation**: Comprehensive notebook documentation with usage examples

## Concrete Deliverables

### 1. Computer Activity Timeline Plot

- **Data Source**: `all_system_events_processed.json` (work sessions)
- **Visualization**: Semi-transparent bars showing computer on/off periods per day
- **Time Granularity**: Daily view with hourly breakdown capability
- **Styling**: Open or semi-transparent bars to allow overlay visibility

### 2. Commit Overlay Markers

- **Data Source**: `commits_processed.json` (processed/corrected timestamps)
- **Visualization**: Markers overlaid on computer activity timeline
- **Styling**: Different markers/colors based on `repo_name`
- **Positioning**: Precise timestamp positioning on timeline

### 3. Dynamic Repository Legend

- **Functionality**: Show only repositories with commits in selected time range
- **Enhancement**: Limit legend to active repos to reduce clutter
- **Interaction**: Update automatically when time range changes

## Technical Requirements

### Jupyter Environment

```python
# Required dependencies for visualization
dependencies = [
    "jupyter>=1.0.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "plotly>=5.15.0",  # For interactive plots
    "ipywidgets>=8.0.0",  # For interactive controls
    "pandas>=2.0.0",  # From TASK-030
    "numpy>=1.24.0"
]
```

### Visualization Components

```python
class TimeBasedVisualizer:
    """Interactive time-based visualization for work session analysis."""

    def __init__(self, analyzer: TimeSeriesAnalyzer):
        """Initialize with time series analyzer."""

    def plot_work_sessions_timeline(self, start_date: str, end_date: str) -> None:
        """Create timeline visualization of work sessions."""

    def plot_commit_frequency(self, period: str = 'day') -> None:
        """Plot commit frequency by time period."""

    def plot_work_vs_commit_correlation(self) -> None:
        """Visualize correlation between work sessions and commits."""

    def create_interactive_dashboard(self) -> None:
        """Create interactive dashboard with zoom controls."""
```

### Notebook Structure

```
notebooks/
├── time_analysis/
│   ├── 01_data_exploration.ipynb          # Initial data exploration
│   ├── 02_work_session_analysis.ipynb     # Work session detection and analysis
│   ├── 03_commit_pattern_analysis.ipynb   # Commit pattern analysis
│   ├── 04_time_range_visualization.ipynb  # Interactive time range visualization
│   └── 05_insights_dashboard.ipynb        # Comprehensive insights dashboard
├── utils/
│   ├── visualization_helpers.py           # Reusable visualization functions
│   └── data_loading_helpers.py            # Data loading utilities
└── README.md                              # Notebook usage documentation
```

### Interactive Features

```python
# Example interactive time range selection
import ipywidgets as widgets
from IPython.display import display

def create_time_range_selector():
    """Create interactive time range selector widget."""
    start_date = widgets.DatePicker(description='Start Date')
    end_date = widgets.DatePicker(description='End Date')
    period = widgets.Dropdown(
        options=['hour', 'day', 'week', 'month'],
        value='day',
        description='Period'
    )

    return widgets.VBox([start_date, end_date, period])

# Example zoom functionality
def plot_with_zoom(data, start_time, end_time, period='day'):
    """Create zoomable plot for specific time range."""
    filtered_data = data[(data.index >= start_time) & (data.index <= end_time)]

    if period == 'hour':
        # Hourly granularity
        plot_data = filtered_data.resample('H').sum()
    elif period == 'day':
        # Daily granularity
        plot_data = filtered_data.resample('D').sum()
    elif period == 'week':
        # Weekly granularity
        plot_data = filtered_data.resample('W').sum()
    elif period == 'month':
        # Monthly granularity
        plot_data = filtered_data.resample('M').sum()

    return plot_data.plot()
```

## Implementation Steps

1. **Environment Setup**

   - Add visualization dependencies to `pyproject.toml`
   - Configure Jupyter notebook environment
   - Set up notebook directory structure

2. **Core Visualization Framework**

   - Create `TimeBasedVisualizer` class
   - Implement basic plotting functions
   - Add interactive widget support

3. **Notebook Development**

   - Create data exploration notebook
   - Develop work session analysis notebook
   - Build commit pattern analysis notebook
   - Create interactive dashboard notebook

4. **Interactive Features**

   - Implement time range selection widgets
   - Add zoom functionality for different time periods
   - Create export capabilities for visualizations

5. **Documentation and Examples**
   - Document notebook usage and examples
   - Create tutorial notebooks for new users
   - Add visualization best practices guide

## Dependencies

- TASK-030 (Pandas Integration for Time-Based Data Analysis)
- Existing system events and commit data
- Jupyter notebook environment
- Visualization libraries (matplotlib, seaborn, plotly)

## Definition of Done

- [x] Jupyter environment configured with all dependencies
- [x] Core visualization framework implemented
- [x] All planned notebooks created and functional
- [x] Interactive features working (zoom, time range selection)
- [x] Export capabilities implemented
- [x] Comprehensive documentation and examples
- [x] Code reviewed and committed

## Estimated Effort

- **Environment Setup**: 2 hours
- **Core Visualization Framework**: 4 hours
- **Notebook Development**: 6 hours
- **Interactive Features**: 3 hours
- **Documentation**: 2 hours
- **Total**: 17 hours

## Related Files

- [project/team/tasks/TASK-030.md](project/team/tasks/TASK-030.md) - Pandas Integration (prerequisite)
- [notebooks/](notebooks/) - Existing notebook directory
- [docs/project/hours/data/](docs/project/hours/data/) - Source data files

## Code Files

- [notebooks/time_analysis/](notebooks/time_analysis/) - New time analysis notebooks
- [notebooks/utils/visualization_helpers.py](notebooks/utils/visualization_helpers.py) - Visualization utilities
- [src/backend/data_analysis/visualizer.py](src/backend/data_analysis/visualizer.py) - Core visualization framework

## Notes

This task completes the time-based analysis infrastructure by providing interactive visualization capabilities. The Jupyter notebook environment will enable users to explore work patterns, validate insights, and generate reports for WBSO compliance and project analysis.
