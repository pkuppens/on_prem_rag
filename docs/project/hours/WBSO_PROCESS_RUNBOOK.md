# WBSO Hours Registration Process Runbook

This runbook provides comprehensive documentation for the WBSO hours registration system, including validation rules, reporting procedures, and re-processing workflows.

## Overview

The WBSO (Wet Bevordering Speur- en Ontwikkelingswerk) hours registration system tracks research and development activities for tax deduction purposes. The system processes work sessions, validates data quality, uploads events to Google Calendar, and generates compliance reports.

## System Architecture

### Data Flow

1. **Data Sources** → **Validation** → **Upload** → **Reporting**
2. **Raw Data**: System events, Git commits, synthetic sessions
3. **Validated Data**: Clean dataset with audit trails
4. **Calendar Events**: Google Calendar entries with WBSO metadata
5. **Reports**: Compliance documentation and hours calculations

### Key Components

- **Data Models**: `WBSOSession`, `CalendarEvent`, `ValidationResult`, `WBSODataset`
- **Validation Script**: `validate_calendar_data.py`
- **Upload Script**: `upload_to_google_calendar.py`
- **Reporting Tool**: `generate_wbso_report.py`

## Data Validation Rules

### Required Fields

All WBSO sessions must have:
- `session_id`: Unique identifier
- `start_time`: Session start (datetime)
- `end_time`: Session end (datetime)
- `work_hours`: Declarable hours (0.0-24.0)
- `date`: ISO date format (YYYY-MM-DD)
- `session_type`: morning/afternoon/evening/full_day
- `is_wbso`: Boolean flag
- `wbso_category`: Valid WBSO category
- `source_type`: "real" or "synthetic"

### WBSO Categories

Valid categories for WBSO eligibility:
- `AI_FRAMEWORK`: AI agent development, NLP, intent recognition
- `ACCESS_CONTROL`: Authentication, authorization, security systems
- `PRIVACY_CLOUD`: Privacy-preserving cloud integration, data protection
- `AUDIT_LOGGING`: Audit logging and system monitoring
- `DATA_INTEGRITY`: Data integrity protection and validation
- `GENERAL_RD`: General research and development activities

### Validation Checks

#### Duplicate Detection
- **Session ID Duplicates**: No duplicate session_ids across all sources
- **DateTime Duplicates**: No identical start+end time combinations
- **Commit Assignment Duplicates**: No duplicate commit assignments

#### Time Range Validation
- **Start < End**: start_time must be before end_time
- **Duration Limits**: Sessions cannot exceed 24 hours
- **Midnight Crossing**: Sessions crossing midnight must have appropriate session_type
- **Timezone Consistency**: All times in Europe/Amsterdam timezone

#### Overlap Detection
- **Critical Overlaps**: >1 hour overlap between WBSO sessions
- **Warning Overlaps**: <1 hour overlap between WBSO sessions
- **Overlap Matrix**: Detailed overlap analysis with duration calculations

#### WBSO Completeness
- **Category Validation**: WBSO category must be one of 6 valid options
- **Justification Required**: All WBSO sessions must have justification text
- **Hours Calculation**: WBSO hours must be properly calculated and documented

#### Data Quality
- **Required Fields**: All required fields must be present and non-empty
- **Hours Validation**: work_hours <= duration_hours
- **Session Type Consistency**: session_type must match time of day
- **Commit Count**: commit_count must match assigned_commits length

## Processing Workflows

### 1. Data Validation Workflow

```bash
# Navigate to scripts directory
cd docs/project/hours/scripts

# Run comprehensive validation
python validate_calendar_data.py

# Check validation results
ls ../validation_output/
```

**Outputs**:
- `validation_report.json`: Full validation results
- `validation_summary.md`: Human-readable summary
- `cleaned_dataset.json`: Validated sessions ready for upload
- `hours_audit_trail.json`: Evidence for hours claims
- `duplicate_sessions.json`: Duplicate detection results
- `overlap_matrix.csv`: Time overlap analysis

**Exit Criteria**:
- Zero critical errors (duplicates, overlaps >1hr, missing WBSO data)
- Documented warnings (acceptable issues)
- Clean dataset with validated hours

### 2. Calendar Upload Workflow

```bash
# Prerequisites: Validation must pass
# Ensure Google Calendar API credentials are configured

# Run upload (dry run first)
python upload_to_google_calendar.py --dry-run

# Run actual upload
python upload_to_google_calendar.py

# Check upload results
ls ../upload_output/
```

**Safety Features**:
- **Target Calendar Verification**: Ensures upload to correct WBSO calendar
- **Duplicate Prevention**: Checks existing events before upload
- **Conflict Detection**: Identifies conflicts with other calendars
- **Batch Processing**: Uploads in batches with rate limiting
- **Error Handling**: Retry logic with exponential backoff
- **Audit Trail**: Complete session_id to event_id mapping

**Outputs**:
- `upload_log.json`: Detailed upload log
- `upload_summary.md`: Human-readable summary
- `session_to_event_mapping.json`: session_id → google_event_id
- `upload_errors.json`: Failed uploads with reasons
- `conflict_report.json`: Time conflicts with other calendars

### 3. Reporting Workflow

```bash
# Generate comprehensive reports
python generate_wbso_report.py

# Check reporting results
ls ../reporting_output/
```

**Outputs**:
- `wbso_sessions.csv`: Detailed session data
- `wbso_category_summary.csv`: Category breakdown
- `wbso_monthly_summary.csv`: Monthly breakdown
- `wbso_report.xlsx`: Excel format report
- `wbso_hours_report.json`: JSON hours data
- `wbso_compliance_documentation.json`: Compliance documentation
- `wbso_summary_report.md`: Human-readable summary

## Re-processing Procedures

### Data Correction Workflow

1. **Identify Issues**: Review validation reports for errors
2. **Correct Source Data**: Fix issues in original data files
3. **Re-run Validation**: Validate corrected data
4. **Re-upload if Needed**: Upload corrected events
5. **Regenerate Reports**: Create updated compliance documentation

### Calendar Event Updates

1. **Identify Events**: Use session_to_event_mapping.json to find events
2. **Update via API**: Use Google Calendar API to modify events
3. **Verify Changes**: Confirm updates in calendar
4. **Update Mapping**: Refresh session_to_event_mapping.json

### Data Source Updates

1. **Add New Sessions**: Add new sessions to appropriate data files
2. **Re-run Validation**: Validate updated dataset
3. **Upload New Events**: Upload only new events (duplicate prevention)
4. **Regenerate Reports**: Create updated reports

## Configuration

### Google Calendar API Setup

1. **Credentials**: Place `credentials.json` in scripts directory
2. **Token**: System will generate `token.json` on first run
3. **Calendar**: Ensure "WBSO Activities 2025" calendar exists
4. **Permissions**: Verify write access to WBSO calendar

### Data File Locations

- **Source Data**: `docs/project/hours/data/`
- **Validation Output**: `docs/project/hours/validation_output/`
- **Upload Output**: `docs/project/hours/upload_output/`
- **Reporting Output**: `docs/project/hours/reporting_output/`

### Configuration Files

- **WBSO Config**: `docs/project/hours/config/wbso_calendar_config.json`
- **Calendar Rules**: `docs/project/hours/config/calendar_categorization_rules.json`
- **Conflict Rules**: `docs/project/hours/config/conflict_detection_rules.json`

## Troubleshooting

### Common Issues

#### Validation Failures
- **Missing Required Fields**: Check data files for complete session data
- **Invalid Time Ranges**: Verify start_time < end_time
- **Duplicate Sessions**: Review duplicate detection reports
- **WBSO Completeness**: Ensure all WBSO sessions have categories and justifications

#### Upload Failures
- **Authentication Issues**: Verify Google Calendar API credentials
- **Calendar Not Found**: Ensure WBSO calendar exists and is accessible
- **Permission Denied**: Verify write access to WBSO calendar
- **Rate Limiting**: Wait and retry if hitting API limits

#### Reporting Issues
- **Missing Data**: Ensure validation and upload completed successfully
- **Excel Export**: Install openpyxl for Excel export functionality
- **File Permissions**: Check write permissions for output directories

### Error Recovery

#### Partial Upload Failures
1. **Review Upload Log**: Check upload_log.json for failed events
2. **Fix Issues**: Address authentication, permission, or data issues
3. **Re-upload**: Run upload script again (duplicate prevention will skip successful uploads)
4. **Verify**: Check session_to_event_mapping.json for completeness

#### Data Corruption
1. **Backup**: Always backup data files before processing
2. **Restore**: Restore from backup if corruption detected
3. **Re-validate**: Re-run validation on restored data
4. **Re-process**: Continue with corrected data

## Compliance Documentation

### WBSO Requirements

- **Minimum Hours**: 510 hours for full tax deduction
- **R&D Activities**: Must qualify as research and development
- **Documentation**: Complete audit trail required
- **Evidence**: Source data must be available for verification

### Audit Trail Components

1. **Session Data**: Complete session information with timestamps
2. **Source Evidence**: System events, Git commits, or synthetic generation
3. **WBSO Justification**: R&D activity descriptions for each session
4. **Category Mapping**: Proper WBSO category assignment
5. **Hours Calculation**: Detailed hours breakdown and verification

### Reporting Requirements

- **Total Hours**: Sum of all WBSO-eligible hours
- **Category Breakdown**: Hours by WBSO category
- **Time Period**: Monthly and weekly breakdowns
- **Source Analysis**: Real vs synthetic hours
- **Compliance Status**: Achievement of 510-hour target

## Maintenance

### Regular Tasks

- **Weekly**: Review validation reports for data quality
- **Monthly**: Generate updated compliance reports
- **Quarterly**: Review and update WBSO categorization rules
- **Annually**: Complete WBSO tax deduction submission

### Data Backup

- **Daily**: Backup data files and configuration
- **Weekly**: Backup validation and upload outputs
- **Monthly**: Archive completed reporting cycles
- **Yearly**: Long-term archive of WBSO documentation

### System Updates

- **Dependencies**: Keep Python packages updated
- **API Changes**: Monitor Google Calendar API changes
- **Configuration**: Update rules and templates as needed
- **Documentation**: Keep runbook current with system changes

## Support

### Documentation

- **Task Documentation**: See TASK-039.md for detailed implementation
- **Code Comments**: Comprehensive inline documentation
- **API Documentation**: Google Calendar API reference
- **WBSO Guidelines**: Official WBSO tax deduction guidelines

### Contact Information

- **Technical Issues**: Review logs and error messages
- **Process Questions**: Consult this runbook and task documentation
- **WBSO Compliance**: Consult tax advisor for WBSO requirements
- **System Maintenance**: Follow maintenance procedures in this runbook

---

**Last Updated**: 2025-01-15  
**Version**: 1.0  
**Maintained By**: AI Assistant  
**Review Cycle**: Quarterly
