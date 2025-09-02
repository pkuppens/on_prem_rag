# WBSO Calendar Integration Testing Scripts

This directory contains comprehensive testing scripts for WBSO calendar integration as specified in the project tasks.

## Scripts Overview

### 1. `test_wbso_calendar_integration.py`

**Main testing script** that implements all requested tasks:

- ✅ **Subtask 1.4**: Test WBSO calendar detection and access
- ✅ **Subtask 1.5**: Test basic CRUD operations on WBSO calendar
- ✅ **Subtask 1.6**: Validate calendar integration is fully functional

### 2. `run_wbso_tests.py`

**Simple test runner** that provides convenient execution of the main test script.

## Features Implemented

### Automated Validation

The script performs comprehensive testing with automated validation:

1. **Calendar Detection**: Automatically finds or creates WBSO calendar
2. **CRUD Operations**: Tests Create, Read, Update, Delete operations
3. **Integration Validation**: Verifies full calendar functionality
4. **Test Record Management**: Creates test event on 2025/05/31 (out of WBSO range)
5. **Independent Operations**: Finds, edits, and deletes records independently
6. **Reproducible Execution**: All tests are automated and repeatable

### Test Event Details

- **Date**: 2025-05-31 (Outside WBSO range for safe testing)
- **Time**: 10:00-12:00 (2-hour test session)
- **Title**: "WBSO Test Event - Integration Testing"
- **Description**: "Test event for WBSO calendar integration validation"
- **Color**: Blue (WBSO activity color scheme)

## Prerequisites

### 1. Google Calendar API Setup

```bash
# Install required dependencies
uv add google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. API Credentials

Download `credentials.json` from Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download `credentials.json` to the scripts directory

### 3. Configuration Files

Ensure these files exist in `../config/`:

- `wbso_calendar_config.json`
- `calendar_categorization_rules.json`

## Usage

### Option 1: Direct Execution

```bash
cd docs/project/hours/scripts
python test_wbso_calendar_integration.py
```

### Option 2: Using Test Runner

```bash
cd docs/project/hours/scripts
python run_wbso_tests.py
```

### Option 3: Using uv (Recommended)

```bash
cd docs/project/hours/scripts
uv run test_wbso_calendar_integration.py
```

## Test Execution Flow

1. **API Setup**: Establishes Google Calendar API access
2. **Calendar Detection**: Finds existing WBSO calendar or creates new one
3. **CRUD Testing**:
   - Creates test event on 2025/05/31
   - Retrieves and verifies event details
   - Updates event with modified information
   - Deletes event and verifies removal
4. **Integration Validation**: Tests calendar properties and event listing
5. **Report Generation**: Creates comprehensive test report

## Output Files

### Test Reports

- `wbso_calendar_test_report.md` - Human-readable test summary
- `wbso_calendar_test_results.json` - Machine-readable test results

### Logs

- `wbso_calendar_test.log` - Detailed execution logs

### Data Files

- All output files are saved to `../data/` directory

## Test Results

### Success Criteria

- ✅ WBSO calendar detected/created successfully
- ✅ All CRUD operations pass (Create, Read, Update, Delete)
- ✅ Calendar integration validation passes
- ✅ Test event created on 2025/05/31 and fully managed

### Failure Handling

- ❌ Detailed error logging for troubleshooting
- ❌ Partial results saved even if some tests fail
- ❌ Clear recommendations for fixing identified issues

## Configuration

### WBSO Calendar Settings

The script uses configuration from `wbso_calendar_config.json`:

- Calendar name: "WBSO Activities 2025"
- Timezone: "Europe/Amsterdam"
- Access level: "private"
- Color scheme: Blue for WBSO activities

### Test Configuration

- Test date: 2025-05-31 (outside WBSO range)
- Event duration: 2 hours (10:00-12:00)
- Event color: Blue (WBSO activity color)

## Troubleshooting

### Common Issues

1. **Missing Credentials**

   ```
   Error: Credentials file not found: credentials.json
   Solution: Download credentials.json from Google Cloud Console
   ```

2. **API Access Denied**

   ```
   Error: Failed to setup API access
   Solution: Check OAuth2 scopes and calendar permissions
   ```

3. **Calendar Not Found**
   ```
   Warning: WBSO calendar not found
   Solution: Script will automatically create new WBSO calendar
   ```

### Debug Mode

Enable detailed logging by modifying the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Integration with Project Tasks

This implementation directly addresses the SCRATCH.md tasks:

```markdown
- [x] **Subtask 1.4**: Test WBSO calendar detection and access
- [x] **Subtask 1.5**: Test basic CRUD operations on WBSO calendar
- [x] **Subtask 1.6**: Validate calendar integration is fully functional
```

## Next Steps

After successful test execution:

1. **Review Test Report**: Check `wbso_calendar_test_report.md`
2. **Verify Calendar**: Check Google Calendar for WBSO calendar
3. **Production Use**: Calendar integration is ready for WBSO activities
4. **Monitoring**: Use generated reports for ongoing validation

## Support

For issues or questions:

1. Check the generated test report and logs
2. Verify Google Calendar API setup
3. Review configuration files
4. Check Google Cloud Console for API quotas and permissions
