# TASK-027: CSV Commit Data Processing to JSON Format

## Story Reference

- **Story**: STORY-008 (WBSO Hours Registration System)
- **Epic**: EPIC-002 (WBSO Compliance and Documentation)

## Task Description

Process CSV commit data files into a structured JSON format for further analysis and integration with work block detection. This task creates a foundation for analyzing commit patterns, identifying work sessions, and detecting commits made outside of work blocks (potentially from different computers).

## Acceptance Criteria

### 1. CSV Processing Pipeline

- [x] **Sub-criteria 1.1**: Process all CSV files in `docs/project/hours/data/commits/` directory
- [x] **Sub-criteria 1.2**: Handle different CSV formats and encodings gracefully
- [x] **Sub-criteria 1.3**: Implement error handling for malformed records

### 2. Data Transformation and Validation

- [x] **Sub-criteria 2.1**: Generate structured JSON records with required fields (timestamp, repo name, author, message, hash)
- [x] **Sub-criteria 2.2**: Identify commits by 'kuppens' (case insensitive substring) for work block analysis
- [x] **Sub-criteria 2.3**: Ensure all required fields are present and properly formatted

### 3. Output Generation and Integration

- [x] **Sub-criteria 3.1**: Create standardized JSON structure for downstream processing
- [x] **Sub-criteria 3.2**: Output format compatible with work block analysis and agenda generation
- [x] **Sub-criteria 3.3**: Include metadata with summary statistics and date ranges

## Technical Requirements

### Input Data

- CSV files in `docs/project/hours/data/commits/` directory
- Expected CSV format: `datetime|timestamp|message|author|hash`
- Multiple repository commit histories (on_prem_rag.csv, healthcare-aigent.csv, etc.)

### Output Format

```json
{
  "commits": [
    {
      "timestamp": "2025-05-30T20:33:36+02:00",
      "repo_name": "on_prem_rag",
      "author": "Pieter Kuppens",
      "message": "Initial commit",
      "hash": "6eb925fc66ad0feabdee45d0f4b3bc2d986c1fcc",
      "is_wbso": true,
      "work_block_id": null,
      "outside_work_block": false
    }
  ],
  "metadata": {
    "total_commits": 150,
    "wbso_commits": 120,
    "repositories": ["on_prem_rag", "healthcare-aigent", "my_chat_gpt"],
    "date_range": {
      "start": "2025-05-30T20:33:36+02:00",
      "end": "2025-01-15T14:22:10+01:00"
    }
  }
}
```

### Processing Rules

1. **Timestamp Parsing**: Convert datetime strings to ISO 8601 format
2. **Repository Detection**: Extract repo name from CSV filename
3. **Author Identification for WBSO**: is_wbso and wbso_commits: is committed by the WBSO holder, and implemented with a case-insensitive matching for 'kuppens' in author field
4. **Data Validation**: Ensure all required fields are present and non-empty
5. **Error Handling**: Log and skip malformed records, continue processing

## Implementation Steps

1. **CSV Processing Pipeline**

   - Create `process_commit_csvs.py` script
   - Implement CSV file discovery and parsing
   - Handle different CSV formats and encodings

2. **Data Transformation**

   - Parse datetime strings to ISO 8601 format
   - Extract repository names from filenames
   - Identify WBSO commits with case-insensitive matching on 'kuppens' in author field to accept both 'pkuppens' and 'Pieter Kuppens'.

3. **JSON Output Generation**

   - Create structured JSON with commits array and metadata
   - Include summary statistics and date ranges
   - Prepare for work block integration

4. **Validation and Testing**
   - Test with existing CSV files
   - Validate JSON output format
   - Ensure error handling works correctly

## Implementation Details

### Architecture Decisions

- **Script Location**: `docs/project/hours/scripts/process_commit_csvs.py` - Located in hours processing scripts directory for logical grouping
- **Data Model Impact**: New `commit` data structure with fields: timestamp, repo_name, author, message, hash, is_wbso, work_block_id, outside_work_block
- **Integration Points**: Output format designed for integration with work block analysis (TASK-025) and agenda generation

### Tool and Dependency Specifications

- **Tool Versions**: Python>=3.12, pandas>=2.0.0 for CSV processing
- **Configuration**: Author filtering rules defined in script constants (case-insensitive 'kuppens' matching)
- **Documentation**: Add CSV processing rules to `docs/project/hours/data/COMMIT_PROCESSING_RULES.md`

### Example Implementation

```python
def process_commit_csvs(csv_directory):
    """Process CSV commit files into structured JSON format.

    Processing rules:
    1. Parse datetime strings to ISO 8601 format
    2. Extract repository names from filenames
    3. Identify WBSO commits with case-insensitive 'kuppens' matching
    4. Validate all required fields are present
    """
    commits = []
    # Implementation details...
    return commits
```

## Dependencies

- CSV files in `docs/project/hours/data/commits/` directory
- Python environment with pandas/csv processing libraries
- Understanding of work block analysis requirements (TASK-025, TASK-026)

## Definition of Done

- [x] CSV processing script completed and tested
- [x] Sample JSON output generated from existing CSV data
- [x] Documentation of processing rules and output format
- [x] Integration points with work block analysis documented
- [x] Error handling covers all edge cases
- [x] Code reviewed and committed to repository

## Estimated Effort

- **CSV Processing Development**: 3 hours
- **Data Transformation Logic**: 2 hours
- **JSON Output Generation**: 1 hour
- **Testing and Validation**: 1 hour
- **Documentation**: 1 hour
- **Total**: 8 hours

## Business Logic Integration

This task prepares data for the following business logic applications:

1. **Work Block Detection**: Commits can be matched against system events work blocks
2. **Outside Work Block Analysis**: Identify commits by Kuppens that fall outside detected work blocks
3. **Computer Detection**: Commits outside work blocks likely indicate different computer usage
4. **Agenda Generation**: Combine commit data with work blocks for comprehensive time tracking

## Related Files

- [docs/project/hours/data/commits/](docs/project/hours/data/commits/) - CSV commit data files
- [project/team/tasks/TASK-025.md](project/team/tasks/TASK-025.md) - System Events Work Block Analysis
- [project/team/tasks/TASK-026.md](project/team/tasks/TASK-026.md) - Integration with Git Commit Analysis

## Code Files

- [docs/project/hours/scripts/process_commit_csvs.py](docs/project/hours/scripts/process_commit_csvs.py) - Main CSV processing script with commit data transformation
- [tests/test_commit_csv_processing.py](tests/test_commit_csv_processing.py) - Unit tests for CSV processing functionality
- [docs/project/hours/data/commits_processed.json](docs/project/hours/data/commits_processed.json) - Generated JSON output from CSV processing

## Notes

This task creates the foundation for comprehensive commit analysis that will integrate with system events work blocks. The JSON output format is designed to be easily consumed by downstream analysis tools for work block correlation and agenda generation.
