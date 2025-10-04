# Unified Datetime Handling System

This document describes the unified datetime handling system implemented for consistent time-based analysis across the project.

## Overview

The unified datetime system provides a standardized approach to handling datetime operations throughout the project. It addresses the fragmentation of datetime parsing functions and establishes a consistent format for time-based analysis.

## Key Features

- **Standardized Format**: `YYYY-MM-DD HH:mm:ss` (24-hour clock, seconds accuracy)
- **Sortable**: Natural lexicographic sorting without special handling
- **No Timezones**: Local user timestamp only
- **Smart Parsing**: Automatic format detection for multiple input formats
- **Backward Compatibility**: Existing code continues to work without changes

## Standard Format

The system uses a single standard format for all datetime operations:

```
YYYY-MM-DD HH:mm:ss
```

Examples:

- `2025-05-03 14:30:45`
- `2025-12-31 23:59:59`
- `2025-01-01 00:00:00`

## String Representation

The default string representation uses ISO format without timezone for better compatibility:

```
YYYY-MM-DDTHH:mm:ss
```

Examples:

- `2025-05-03T14:30:45`
- `2025-12-31T23:59:59`
- `2025-01-01T00:00:00`

### Why This Format?

1. **Sortable**: Strings sort correctly in lexicographic order
2. **Readable**: Human-readable format
3. **Consistent**: Same format across all operations
4. **No Timezones**: Eliminates timezone complexity
5. **Precise**: Second-level accuracy for most use cases

## Supported Input Formats

The system can parse these existing formats found in the codebase:

| Format                   | Example                            | Description                               |
| ------------------------ | ---------------------------------- | ----------------------------------------- |
| `%m/%d/%Y %I:%M:%S %p`   | `5/9/2025 8:08:14 PM`              | System events format                      |
| `%Y/%m/%d %H:%M:%S`      | `2025/06/24 07:30:54`              | Alternative date format                   |
| `%Y-%m-%d %H:%M:%S`      | `2025-06-24 07:30:54`              | Standard format                           |
| `%Y-%m-%dT%H:%M:%S`      | `2025-06-24T07:30:54`              | ISO format without timezone               |
| `%Y-%m-%dT%H:%M:%S%z`    | `2025-06-24T07:30:54+02:00`        | ISO format with timezone                  |
| `%Y-%m-%dT%H:%M:%S.%f`   | `2025-06-24T07:30:54.123456`       | ISO format with microseconds              |
| `%Y-%m-%dT%H:%M:%S.%f%z` | `2025-06-24T07:30:54.123456+02:00` | ISO format with microseconds and timezone |

## Core Classes and Functions

### UnifiedDateTime Class

The main class for datetime operations:

```python
from src.backend.datetime_utils import UnifiedDateTime

# Create from string
dt = UnifiedDateTime("2025-05-03 14:30:45")

# Create from datetime object
dt = UnifiedDateTime(datetime(2025, 5, 3, 14, 30, 45))

# Create with current time
dt = UnifiedDateTime()

# Get standard format string
standard_str = dt.to_standard_format()  # "2025-05-03 14:30:45"

# Get ISO format string (default string representation)
iso_str = dt.to_iso_format()  # "2025-05-03T14:30:45"
str(dt)  # "2025-05-03T14:30:45" (same as to_iso_format)

# Get datetime object
dt_obj = dt.to_datetime()

# Check if valid
is_valid = dt.is_valid()

# Parse flexible format
dt = UnifiedDateTime.parse_flexible("5/9/2025 8:08:14 PM")
```

### Backward Compatibility Functions

For existing code that uses the old `parse_datetime_flexible` function:

```python
from src.backend.datetime_utils import parse_datetime_flexible

# This function still works exactly as before
dt = parse_datetime_flexible("2025-05-03 14:30:45")
# Returns datetime object or None
```

### Utility Functions

```python
from src.backend.datetime_utils import (
    convert_to_standard_format,
    validate_datetime_format
)

# Convert any input to standard format
standard_str = convert_to_standard_format("5/9/2025 8:08:14 PM")
# Returns "2025-05-09 20:08:14"

# Validate datetime string
is_valid = validate_datetime_format("2025-05-03 14:30:45")
# Returns True or False
```

## Usage Examples

### Basic Usage

```python
from src.backend.datetime_utils import UnifiedDateTime

# Parse various formats
formats = [
    "2025-05-03 14:30:45",      # Standard format
    "5/9/2025 8:08:14 PM",      # System events format
    "2025-06-24T07:30:54+02:00", # Git commit format
]

for dt_str in formats:
    dt = UnifiedDateTime(dt_str)
    if dt.is_valid():
        print(f"Input: {dt_str}")
        print(f"Standard: {dt.to_standard_format()}")
        print(f"Datetime: {dt.to_datetime()}")
        print()
```

### Sorting and Comparison

```python
# Create list of datetime strings
dt_strings = [
    "2025-05-03 15:30:45",
    "2025-05-03 14:30:45",
    "2025-05-04 14:30:45",
]

# Convert to UnifiedDateTime objects
dt_objects = [UnifiedDateTime(dt_str) for dt_str in dt_strings]

# Sort by standard format (lexicographic = chronological)
sorted_dts = sorted(dt_objects, key=lambda x: x.to_standard_format())

# Or sort by datetime object
sorted_dts = sorted(dt_objects, key=lambda x: x.to_datetime())
```

### Data Processing

```python
# Process CSV data with various datetime formats
import csv
from src.backend.datetime_utils import UnifiedDateTime

def process_csv_with_datetime(csv_file):
    results = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse datetime from any format
            dt = UnifiedDateTime(row['timestamp'])

            if dt.is_valid():
                # Convert to standard format for consistency
                row['standard_timestamp'] = dt.to_standard_format()
                results.append(row)
            else:
                print(f"Invalid datetime: {row['timestamp']}")

    return results
```

## Migration Guide

### For Existing Code

If you have existing code using `parse_datetime_flexible`, no changes are needed:

```python
# This still works exactly as before
from src.backend.datetime_utils import parse_datetime_flexible

dt = parse_datetime_flexible("2025-05-03 14:30:45")
```

### For New Code

Use the new `UnifiedDateTime` class for better functionality:

```python
# Old way (still works)
from src.backend.datetime_utils import parse_datetime_flexible
dt = parse_datetime_flexible("2025-05-03 14:30:45")

# New way (recommended)
from src.backend.datetime_utils import UnifiedDateTime
dt = UnifiedDateTime("2025-05-03 14:30:45")
```

### Updating Imports

If you have local `parse_datetime_flexible` functions, replace them with imports:

```python
# Old way - local function
def parse_datetime_flexible(dt_str: str) -> Optional[datetime]:
    # ... local implementation

# New way - import from unified system
from src.backend.datetime_utils import parse_datetime_flexible
```

## Error Handling

The system handles various error conditions gracefully:

```python
from src.backend.datetime_utils import UnifiedDateTime

# Invalid input types
dt = UnifiedDateTime(123)  # Invalid type
assert not dt.is_valid()

# Invalid datetime strings
dt = UnifiedDateTime("not a datetime")
assert not dt.is_valid()

# Empty strings
dt = UnifiedDateTime("")
assert not dt.is_valid()

# Malformed datetime strings
dt = UnifiedDateTime("2025-13-01 25:70:80")
assert not dt.is_valid()
```

## Performance Considerations

- **Parsing**: Efficient format detection with early exit on success
- **Memory**: Minimal memory overhead for datetime objects
- **Large Datasets**: Tested with 1000+ datetime strings
- **Caching**: No caching implemented (consider for very large datasets)

## Testing

The system includes comprehensive tests covering:

- All supported input formats
- Error handling and edge cases
- Performance with large datasets
- Backward compatibility
- Comparison operations
- String representations

Run tests with:

```bash
uv run pytest tests/test_datetime_utils.py -v
```

## Future Enhancements

Potential improvements for future versions:

1. **Format Caching**: Cache successful format patterns for better performance
2. **Custom Formats**: Allow registration of custom datetime formats
3. **Timezone Support**: Optional timezone handling for specific use cases
4. **Batch Processing**: Optimized parsing for large datasets
5. **Validation Rules**: Configurable validation rules for datetime ranges

## Code Files

- [src/backend/datetime_utils.py](src/backend/datetime_utils.py) - Main implementation
- [tests/test_datetime_utils.py](tests/test_datetime_utils.py) - Comprehensive test suite
- [src/backend/session_detection.py](src/backend/session_detection.py) - Updated to use unified system
- [docs/project/hours/scripts/](docs/project/hours/scripts/) - Scripts updated to use unified system

## References

- [project/team/tasks/TASK-029.md](project/team/tasks/TASK-029.md) - Task requirements and implementation details
- [Python datetime documentation](https://docs.python.org/3/library/datetime.html)
- [ISO 8601 standard](https://en.wikipedia.org/wiki/ISO_8601)
