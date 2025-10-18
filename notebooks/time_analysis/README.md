# Time-Based Analysis Notebooks

This directory contains Jupyter notebooks for interactive time-based visualization and analysis of work sessions and commit patterns.

## Overview

The notebooks provide interactive visualizations showing:

- **Computer Activity Timeline**: Semi-transparent bars showing when the computer was on/off
  - X-axis: Dates (horizontal timeline)
  - Y-axis: Time of day (0-24 hours)
- **Commit Overlay**: Repository-specific markers overlaid on the timeline at precise timestamps
- **Dynamic Legend**: Shows only active repositories in the selected time range
- **Daily Summary**: Statistical overview of daily activity patterns

## Data Sources

- **System Events**: `docs/project/hours/data/all_system_events_processed.json`
- **Commits**: `docs/project/hours/data/commits_processed.json`

## Notebooks

### 01_computer_activity_timeline.ipynb

Main visualization notebook that creates:

- Computer activity timeline with semi-transparent bars
- Commit markers overlaid with repository-specific styling
- Dynamic legend showing only active repositories
- Daily activity summary charts
- Repository activity analysis

## Usage

### Prerequisites

1. **Dependencies**: Ensure all required packages are installed:

   ```bash
   uv sync --dev
   ```

2. **Data Files**: Ensure the data files exist:
   - `docs/project/hours/data/all_system_events_processed.json`
   - `docs/project/hours/data/commits_processed.json`

### Running the Notebooks

1. **Start Jupyter**: From the project root:

   ```bash
   uv run jupyter notebook
   ```

2. **Navigate**: Go to `notebooks/time_analysis/01_computer_activity_timeline.ipynb`

3. **Configure Time Range**: Modify the `start_date` and `end_date` variables in the notebook to focus on specific periods

4. **Run All Cells**: Execute all cells to generate the visualizations

### Customization

#### Time Range Selection

```python
# Modify these dates to focus on specific periods
start_date = "2025-06-01"
end_date = "2025-08-31"
```

#### Repository Filtering

The notebook automatically filters to show only repositories with commits in the selected time range. This keeps the legend clean and focused.

#### Export Options

Visualizations are automatically saved to `notebooks/time_analysis/outputs/` with descriptive filenames.

## Features Implemented

### ✅ Computer Activity Timeline

- Semi-transparent bars showing work session periods
- Daily view with hourly breakdown capability
- Proper timezone handling for accurate visualization

### ✅ Commit Overlay Markers

- Repository-specific colors and markers
- Precise timestamp positioning on timeline
- Overlay on computer activity bars

### ✅ Dynamic Repository Legend

- Shows only repositories with commits in selected time range
- Reduces legend clutter
- Updates automatically when time range changes

### ✅ Interactive Time Range Selection

- Easy modification of start and end dates
- Automatic filtering of data to selected range
- Real-time updates of visualizations

### ✅ Export Capabilities

- High-quality PNG exports (300 DPI)
- Descriptive filenames with date ranges
- Organized output directory structure

## Output Files

The notebooks generate several output files:

- `computer_activity_timeline_YYYY-MM-DD_to_YYYY-MM-DD.png` - Main timeline visualization
- `daily_activity_summary_YYYY-MM-DD_to_YYYY-MM-DD.png` - Daily summary charts
- `test_timeline_plot.png` - Test visualization (from test script)

## Technical Details

### Data Processing

- **Timezone Handling**: All timestamps are normalized to UTC for consistent comparison
- **Data Filtering**: Efficient filtering by date range and active repositories
- **Memory Management**: Optimized for large datasets with proper DataFrame operations

### Visualization Components

- **Matplotlib**: Core plotting library with custom styling
- **Seaborn**: Color palettes and statistical visualizations
- **Pandas**: Data manipulation and time series operations

### Performance Considerations

- **Lazy Loading**: Data is loaded only when needed
- **Efficient Filtering**: Date range filtering before visualization
- **Memory Optimization**: Proper DataFrame operations to minimize memory usage

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root and have installed dev dependencies:

   ```bash
   uv sync --dev
   ```

2. **Data File Not Found**: Verify the data files exist in the correct location:

   ```bash
   ls docs/project/hours/data/
   ```

3. **Timezone Issues**: The notebooks handle timezone conversion automatically. If you encounter issues, ensure your system timezone is set correctly.

4. **Memory Issues**: For very large datasets, consider:
   - Reducing the time range
   - Filtering to specific repositories
   - Using smaller figure sizes

### Testing

Run the test script to verify everything is working:

```bash
uv run python notebooks/test_visualization.py
```

## Related Documentation

- [TASK-031.md](../../project/team/tasks/TASK-031.md) - Task specification and requirements
- [TASK-030.md](../../project/team/tasks/TASK-030.md) - Pandas integration (prerequisite)
- [Data Analysis Documentation](../../docs/technical/) - Technical implementation details

## Future Enhancements

Potential improvements for future versions:

- Interactive widgets for real-time time range selection
- Zoom functionality for detailed time period analysis
- Export to multiple formats (PDF, SVG, HTML)
- Integration with Jupyter widgets for enhanced interactivity
- Real-time data updates from live system events
