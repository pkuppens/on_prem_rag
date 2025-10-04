# TASK-032: Smart Datetime Parsing System for Multiple Data Sources

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## Task Description

Implement a smart datetime parsing system that can automatically detect and convert datetime formats from various data sources. This system will handle the diverse datetime formats found in system events, git commits, and other data sources with intelligent format detection and conversion.

## Business Context

Different data sources use different datetime formats, making data integration challenging. A smart parsing system will automatically detect formats and convert them to the unified standard, reducing manual configuration and improving data quality across the project.

## Acceptance Criteria

- [ ] **Format Auto-Detection**: Automatically detect datetime formats from input strings
- [ ] **Multi-Source Support**: Handle formats from system events, git commits, CSV files, and JSON data
- [ ] **Robust Error Handling**: Graceful handling of malformed or ambiguous datetime strings
- [ ] **Performance Optimization**: Efficient parsing suitable for large datasets
- [ ] **Format Validation**: Validate detected formats before conversion
- [ ] **Logging and Debugging**: Comprehensive logging for format detection and conversion
- [ ] **Integration Testing**: Test with real data from all sources

## Technical Requirements

### Smart Parser Design

```python
class SmartDatetimeParser:
    """Intelligent datetime parser with automatic format detection."""

    def __init__(self):
        """Initialize with common format patterns."""
        self.format_patterns = {
            # System events formats
            'system_events': [
                "%m/%d/%Y %I:%M:%S %p",  # 5/9/2025 8:08:14 PM
                "%Y/%m/%d %H:%M:%S",     # 2025/06/24 07:30:54
            ],
            # Git commit formats
            'git_commits': [
                "%Y-%m-%dT%H:%M:%S%z",   # 2025-06-24T07:30:54+02:00
                "%Y-%m-%dT%H:%M:%S",     # 2025-06-24T07:30:54
            ],
            # Standard formats
            'standard': [
                "%Y-%m-%d %H:%M:%S",     # 2025-06-24 07:30:54
                "%Y-%m-%dT%H:%M:%S",     # 2025-06-24T07:30:54
            ]
        }

    def detect_format(self, datetime_str: str, source_type: str = None) -> Optional[str]:
        """Detect the most likely datetime format for the input string."""

    def parse_with_detection(self, datetime_str: str, source_type: str = None) -> Optional[datetime]:
        """Parse datetime string with automatic format detection."""

    def validate_format(self, datetime_str: str, format_str: str) -> bool:
        """Validate if datetime string matches the specified format."""

    def get_detection_confidence(self, datetime_str: str, format_str: str) -> float:
        """Get confidence score for format detection."""
```

### Format Detection Algorithm

```python
def detect_datetime_format(datetime_str: str, source_type: str = None) -> Dict[str, Any]:
    """Detect datetime format with confidence scoring.

    Args:
        datetime_str: Input datetime string
        source_type: Optional hint about data source type

    Returns:
        Dictionary with detected format, confidence score, and metadata
    """
    candidates = []

    # Get relevant format patterns based on source type
    patterns = get_patterns_for_source(source_type)

    for pattern in patterns:
        try:
            parsed = datetime.strptime(datetime_str, pattern)
            confidence = calculate_confidence(datetime_str, pattern, parsed)
            candidates.append({
                'format': pattern,
                'confidence': confidence,
                'parsed': parsed,
                'source_type': source_type
            })
        except ValueError:
            continue

    # Return best candidate
    if candidates:
        best = max(candidates, key=lambda x: x['confidence'])
        return best

    return None

def calculate_confidence(datetime_str: str, format_str: str, parsed: datetime) -> float:
    """Calculate confidence score for format detection."""
    score = 1.0

    # Penalize formats that don't use all characters
    if len(datetime_str) != len(parsed.strftime(format_str)):
        score *= 0.8

    # Bonus for formats that match expected patterns
    if re.match(r'^\d{4}-\d{2}-\d{2}', datetime_str):
        score *= 1.1  # ISO-like format bonus

    # Penalize very old or future dates
    current_year = datetime.now().year
    if parsed.year < 2020 or parsed.year > current_year + 1:
        score *= 0.7

    return score
```

### Data Source Integration

```python
class DataSourceParser:
    """Parser for specific data sources with format hints."""

    def __init__(self, source_type: str):
        """Initialize with data source type."""
        self.source_type = source_type
        self.parser = SmartDatetimeParser()

    def parse_system_event_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse system event timestamp with source-specific logic."""

    def parse_git_commit_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse git commit timestamp with timezone handling."""

    def parse_csv_timestamp(self, timestamp_str: str, column_name: str = None) -> Optional[datetime]:
        """Parse CSV timestamp with column name hints."""

    def parse_json_timestamp(self, timestamp_str: str, field_name: str = None) -> Optional[datetime]:
        """Parse JSON timestamp with field name hints."""
```

## Implementation Steps

1. **Core Parser Development**

   - Create `SmartDatetimeParser` class
   - Implement format detection algorithm
   - Add confidence scoring system

2. **Data Source Integration**

   - Create `DataSourceParser` for different source types
   - Implement source-specific parsing logic
   - Add format validation and error handling

3. **Performance Optimization**

   - Implement format caching for repeated patterns
   - Add batch processing capabilities
   - Optimize for large dataset processing

4. **Testing and Validation**

   - Create comprehensive test suite with real data
   - Test format detection accuracy
   - Validate performance with large datasets

5. **Integration with Existing Code**
   - Replace existing parsing functions
   - Update data loading utilities
   - Ensure compatibility with unified datetime system

## Dependencies

- TASK-029 (Unified Datetime Handling System)
- Existing datetime parsing functions
- System events and commit data files
- Python datetime and regex modules

## Definition of Done

- [ ] Smart datetime parser implemented and tested
- [ ] Format auto-detection working with >95% accuracy
- [ ] Data source integration completed
- [ ] Performance optimized for large datasets
- [ ] Comprehensive test suite with real data
- [ ] Integration with existing code completed
- [ ] Documentation updated with usage examples
- [ ] Code reviewed and committed

## Estimated Effort

- **Core Parser Development**: 4 hours
- **Data Source Integration**: 3 hours
- **Performance Optimization**: 2 hours
- **Testing and Validation**: 3 hours
- **Integration**: 2 hours
- **Documentation**: 1 hour
- **Total**: 15 hours

## Related Files

- [project/team/tasks/TASK-029.md](project/team/tasks/TASK-029.md) - Unified Datetime System (prerequisite)
- [src/backend/session_detection.py](src/backend/session_detection.py) - Current parsing functions
- [docs/project/hours/scripts/](docs/project/hours/scripts/) - Scripts with datetime parsing

## Code Files

- [src/backend/datetime_utils/smart_parser.py](src/backend/datetime_utils/smart_parser.py) - Smart parsing system
- [src/backend/datetime_utils/data_source_parser.py](src/backend/datetime_utils/data_source_parser.py) - Data source integration
- [tests/test_smart_parser.py](tests/test_smart_parser.py) - Smart parser testing

## Notes

This task enhances the unified datetime system with intelligent format detection, making it easier to integrate data from various sources. The smart parsing system will significantly improve data quality and reduce manual configuration requirements.
