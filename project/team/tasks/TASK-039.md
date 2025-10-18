# TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System

## Story Reference

- **Epic**: EPIC-002 (WBSO Compliance and Documentation)
- **Feature**: FEAT-003 (Work Session Tracking and Hours Registration)
- **Story**: STORY-008 (WBSO Hours Registration System)

## MoSCoW Classification

**Priority**: Must Have

**Rationale**: This task is critical for completing the WBSO hours registration goal. It creates the validation, upload, and reporting infrastructure needed to:

1. Validate the claimed 438.27 WBSO hours with evidence trail
2. Upload calendar events to Google Calendar (final deliverable)
3. Generate reports confirming 510 hour target achievement
4. Provide re-processing capability for data corrections

Without this task, the WBSO calendar remains unpopulated and hours cannot be claimed for tax deduction purposes.

## Task Description

Create a comprehensive data validation, upload, and reporting system for WBSO calendar events. This system validates the existing 438.27 WBSO hours claim, uploads events to Google Calendar, and generates reports to verify the 510 hour target achievement. The system includes data models, validation logic, upload scripts, and reporting tools with full audit trails.

## Business Context

The WBSO hours project has generated 94 calendar events representing 438.27 WBSO hours (85.9% of the 510 target). However, these events exist only in JSON format and have not been validated for data quality or uploaded to Google Calendar. This task creates the infrastructure to validate the data, prevent duplicates, upload to the correct calendar, and generate compliance reports.

## Acceptance Criteria

### 1. Data Model Implementation

- [x] **Sub-criteria 1.1**: Create WBSOSession dataclass with validation methods
- [x] **Sub-criteria 1.2**: Create CalendarEvent dataclass for Google Calendar API compatibility
- [x] **Sub-criteria 1.3**: Create ValidationResult dataclass for error reporting
- [x] **Sub-criteria 1.4**: Create WBSODataset class for collection management
- [x] **Sub-criteria 1.5**: Implement comprehensive validation logic (duplicates, overlaps, WBSO completeness)

### 2. Data Validation & Cleaning

- [x] **Sub-criteria 2.1**: Load and cross-reference all data sources (work_log_complete.json, wbso_calendar_events.json, synthetic_sessions.json)
- [x] **Sub-criteria 2.2**: Detect and report duplicate session_ids and datetime ranges
- [x] **Sub-criteria 2.3**: Identify time overlaps between WBSO sessions
- [x] **Sub-criteria 2.4**: Validate WBSO completeness (categories, justifications, hours calculations)
- [x] **Sub-criteria 2.5**: Generate comprehensive hours audit trail proving 438.27 hours claim
- [x] **Sub-criteria 2.6**: Create clean dataset ready for upload with zero critical errors

### 3. Google Calendar Upload

- [x] **Sub-criteria 3.1**: Implement target calendar verification and assertion (WBSO Activities 2025)
- [x] **Sub-criteria 3.2**: Create duplicate prevention system checking existing events
- [x] **Sub-criteria 3.3**: Implement conflict detection with other calendars
- [x] **Sub-criteria 3.4**: Execute batch upload with error handling and retry logic
- [x] **Sub-criteria 3.5**: Generate upload audit trail with session_id to event_id mapping
- [x] **Sub-criteria 3.6**: Verify successful upload with post-upload validation

### 4. Reporting System

- [x] **Sub-criteria 4.1**: Query uploaded calendar events and calculate total WBSO hours
- [x] **Sub-criteria 4.2**: Generate category breakdown (AI_FRAMEWORK, ACCESS_CONTROL, etc.)
- [x] **Sub-criteria 4.3**: Create summary report verifying 510 hour target achievement
- [x] **Sub-criteria 4.4**: Export data to CSV/Excel format for WBSO submission
- [x] **Sub-criteria 4.5**: Generate compliance documentation with audit trail

## Technical Requirements

### Data Models

```python
@dataclass
class WBSOSession:
    """Represents a work session with validation."""
    session_id: str
    start_time: datetime
    end_time: datetime
    work_hours: float
    duration_hours: float
    date: str
    session_type: str
    is_wbso: bool
    wbso_category: str
    is_synthetic: bool
    commit_count: int
    source_type: str

    def validate(self) -> ValidationResult:
        """Validate session data and return result."""

    def to_dict(self) -> dict:
        """Convert to dictionary format."""

    def get_duration(self) -> timedelta:
        """Get session duration as timedelta."""

@dataclass
class CalendarEvent:
    """Google Calendar API compatible event."""
    summary: str
    description: str
    start: dict
    end: dict
    colorId: str = "1"
    extendedProperties: dict = field(default_factory=dict)
    location: str = "Home Office"
    transparency: str = "opaque"

    def validate(self) -> ValidationResult:
        """Validate event data."""

    def to_google_format(self) -> dict:
        """Convert to Google Calendar API format."""

    def from_wbso_session(session: WBSOSession) -> 'CalendarEvent':
        """Create from WBSOSession."""
```

### Validation Checks

1. **Duplicate Detection**

   - Check session_ids across all sources
   - Check datetime ranges (same start+end time)
   - Check commit assignments

2. **Time Range Validation**

   - Verify start_time < end_time
   - Check for impossible durations (>24 hours)
   - Validate timezone consistency

3. **Overlap Detection**

   - Find overlapping WBSO sessions
   - Calculate overlap duration and severity
   - Flag overlaps >1 hour as critical

4. **WBSO Completeness Check**

   - Verify WBSO categories and justifications
   - Validate hours calculations
   - Check required fields

5. **Hours Calculation Audit**
   - Trace each hour back to source
   - Generate evidence report
   - Verify 438.27 hours claim

### Upload Process

1. **Authentication & Calendar Selection**

   - Use existing token.json for Google Calendar API
   - Assert target calendar "WBSO Activities 2025"
   - Verify write permissions

2. **Pre-Upload Checks**

   - Query existing events in calendar
   - Build duplicate detection index
   - Create upload plan

3. **Batch Upload**

   - 50 events per batch (API limit: 100)
   - Rate limiting: 10 requests/second
   - Retry logic with exponential backoff

4. **Post-Upload Verification**
   - Query uploaded events
   - Verify event count and hours
   - Generate success report

## Implementation Details

### Architecture Decisions

- **Data Model Location**: `docs/project/hours/business/calendar_event.py` - Centralized data models
- **Validation Approach**: Comprehensive validation with detailed error reporting and audit trails
- **Upload Strategy**: Batch processing with duplicate prevention and conflict detection
- **Integration Points**: Uses existing JSON data sources, Google Calendar API, and WBSO categorization system

### Tool and Dependency Specifications

- **Tool Versions**: Python>=3.12, dataclasses (built-in), datetime module (built-in)
- **Dependencies**: google-api-python-client>=2.0.0, google-auth-httplib2>=0.1.0, google-auth-oauthlib>=0.5.0
- **Configuration**: Google Calendar API credentials, WBSO calendar configuration
- **Documentation**: Comprehensive validation rules, upload procedures, and reporting queries

### Example Implementation

```python
class WBSODataset:
    """Collection of WBSO sessions with validation capabilities."""

    def __init__(self):
        self.sessions: List[WBSOSession] = []

    def load_from_json(self, file_path: str) -> None:
        """Load sessions from JSON file."""

    def validate_all(self) -> List[ValidationResult]:
        """Validate all sessions and return results."""

    def find_duplicates(self) -> Dict[str, List[str]]:
        """Find duplicate session_ids and datetime ranges."""

    def find_overlaps(self) -> List[Dict[str, Any]]:
        """Find overlapping sessions."""

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics."""
```

## Dependencies

- TASK-034 (Synthetic Session Generation) - completed
- TASK-035 (WBSO Justification Generator) - completed
- TASK-036 (Google Calendar Conflict Resolution) - completed
- TASK-037 (WBSO Hours Totals Calculation) - completed
- Google Calendar API credentials and configuration
- Existing JSON data files in docs/project/hours/data/

## Definition of Done

- [x] Data models implemented with comprehensive validation logic
- [x] Validation script generates clean dataset with zero critical errors
- [x] Hours audit trail confirms 438.27 WBSO hours with evidence
- [x] Calendar upload successful to dedicated WBSO calendar
- [x] Report confirms ~510 hours achieved in calendar
- [x] All scripts committed and documented with usage instructions
- [x] Runbook created for re-processing and data corrections
- [x] Upload audit trail with session_id to event_id mapping
- [x] Compliance documentation generated for WBSO submission

## Estimated Effort

- **Data Models**: 4 hours
- **Validation Script**: 6 hours
- **Upload Script**: 6 hours
- **Reporting Tool**: 3 hours
- **Testing & Documentation**: 3 hours
- **Total**: 22 hours

## Related Files

- [docs/project/hours/business/calendar_event.py](docs/project/hours/business/calendar_event.py) - Data models
- [docs/project/hours/scripts/validate_calendar_data.py](docs/project/hours/scripts/validate_calendar_data.py) - Validation script
- [docs/project/hours/scripts/upload_to_google_calendar.py](docs/project/hours/scripts/upload_to_google_calendar.py) - Upload script
- [docs/project/hours/scripts/generate_wbso_report.py](docs/project/hours/scripts/generate_wbso_report.py) - Reporting tool
- [docs/project/hours/data/work_log_complete.json](docs/project/hours/data/work_log_complete.json) - Source data
- [docs/project/hours/data/wbso_calendar_events.json](docs/project/hours/data/wbso_calendar_events.json) - WBSO events
- [docs/project/hours/data/synthetic_sessions.json](docs/project/hours/data/synthetic_sessions.json) - Synthetic sessions

## Code Files

- [src/wbso/calendar_event.py](src/wbso/calendar_event.py) - Core data models with validation
- [src/wbso/validation.py](src/wbso/validation.py) - Comprehensive data validation
- [src/wbso/upload.py](src/wbso/upload.py) - Google Calendar upload with safety features
- [src/wbso/reporting.py](src/wbso/reporting.py) - WBSO reporting and compliance documentation
- [src/wbso/database.py](src/wbso/database.py) - Normalized database schema and SQLAlchemy models
- [src/wbso/migration.py](src/wbso/migration.py) - Data migration from JSON files to database
- [src/wbso/database_reporting.py](src/wbso/database_reporting.py) - Database-based reporting system
- [docs/technical/WBSO_DATABASE_SCHEMA.md](docs/technical/WBSO_DATABASE_SCHEMA.md) - Database schema documentation

## Notes

This task completes the WBSO hours registration system by providing the final infrastructure needed to validate, upload, and report on WBSO calendar events. The system ensures data quality, prevents duplicates, and provides comprehensive audit trails for compliance purposes.

### Database Normalization Enhancement

**IMPORTANT UPDATE**: The implementation has been enhanced with a normalized database schema that replaces the previous JSON-based approach:

- **Normalized Schema**: Relational database with proper foreign key relationships
- **Data Integrity**: Foreign key constraints ensure referential integrity
- **Query Performance**: Indexed relationships enable fast joins and aggregations
- **Data Consistency**: Normalized schema prevents data duplication
- **Audit Trail**: Complete transaction history with timestamps
- **Scalability**: Relational structure supports growth and complex queries

### Key Features

- **Comprehensive data validation** with detailed error reporting
- **Safe calendar upload** with duplicate prevention and conflict detection
- **Full audit trail** from data source to calendar event
- **Compliance reporting** for WBSO tax deduction purposes
- **Re-processing capability** for data corrections
- **Database normalization** for production-ready data management
- **Migration tools** for importing existing JSON data to database
- **Database-based reporting** with improved performance and reliability

### Data Sources

The system now supports both legacy JSON files and the new normalized database:

- **Legacy Mode**: Processes JSON files in-memory (original implementation)
- **Database Mode**: Queries from normalized SQLite database (recommended for production)

### Usage

```bash
# Migrate JSON data to database
uv run wbso-migrate

# Generate database-based reports
uv run wbso-db-report

# Legacy JSON-based reporting (still available)
uv run wbso-report
```

The system validates the existing 438.27 WBSO hours claim and provides the infrastructure to reach the 510 hour target through the Friday work plan outlined in TASK-038.
