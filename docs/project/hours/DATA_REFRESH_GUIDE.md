# WBSO Data Refresh Guide

**Document Version**: 1.0  
**Created**: 2025-11-28  
**Last Updated**: 2025-11-28

## Overview

This guide explains how to manually refresh WBSO data sources (system events and git commits) and how the automated pipeline handles data refresh.

## Data Sources

The WBSO pipeline requires two primary data sources:

1. **System Events** - Windows event logs (computer on/off, user logon/logoff)
2. **Git Commits** - Commit history from multiple repositories

## Manual Data Refresh Process

### 1. System Events Extraction

#### Purpose

Extract Windows event logs to track computer activity and work session boundaries.

#### Prerequisites

- Windows PowerShell (run as Administrator for full event log access)
- Access to Windows Event Logs (System and Security logs)

#### Step-by-Step Process

1. **Navigate to Scripts Directory**

   ```powershell
   cd docs\project\hours\scripts
   ```

2. **Run System Events Extraction**

   ```powershell
   .\Extract-SystemEvents.ps1
   ```

   **Optional Parameters:**

   ```powershell
   # Extract events for specific date range
   .\Extract-SystemEvents.ps1 -StartDate "2025-11-01" -EndDate "2025-11-28"

   # Specify custom output path
   .\Extract-SystemEvents.ps1 -OutputPath ".\data\system_events_custom.csv"
   ```

3. **Verify Output**
   - Check that file was created in the data directory: `docs\project\hours\data\system_events_YYYYMMDD.csv`
   - The script automatically outputs to the data directory (relative to scripts directory)
   - Verify file contains events (open CSV and check row count)
   - Check for errors in PowerShell output

#### What Gets Extracted

The script extracts the following Windows Event IDs:

**System Events:**

- **6005**: System startup (Event Log service started)
- **6006**: System shutdown (Event Log service stopped)
- **6008**: Unexpected shutdown
- **1074**: System shutdown/restart initiated
- **41**: System rebooted without cleanly shutting down
- **6013**: System uptime report
- **42**: System entering sleep

**Security Events:**

- **4624**: Successful logon
- **4625**: Failed logon attempt
- **4634**: Account logoff
- **4647**: User initiated logoff
- **4648**: Logon using explicit credentials

#### Output Format

CSV file with columns:

- `DateTime` - Event timestamp (YYYY/MM/DD HH:MM:SS)
- `EventId` - Windows Event ID
- `LogName` - Event log source (System/Security)
- `EventType` - Description of event type
- `Level` - Event severity
- `Username` - User associated with event
- `ProcessName` - Process that triggered event
- `Message` - Detailed event description
- `AdditionalInfo` - Additional event details
- `RecordId` - Unique event record ID

#### Troubleshooting

**Issue: "Access Denied" errors**

- **Solution**: Run PowerShell as Administrator
- Some Security log events require elevated privileges

**Issue: No events found**

- **Solution**: Check date range - events may not exist for specified period
- Verify event logs are enabled and contain data

**Issue: Script runs but produces empty file**

- **Solution**: Check event log permissions
- Verify date range includes actual system activity

### 2. Git Commits Extraction

#### Purpose

Extract commit history from all configured repositories for WBSO hours tracking.

#### Prerequisites

- Git installed and accessible from PowerShell
- All repositories cloned to local filesystem
- `repositories.csv` file configured with repository list

#### Step-by-Step Process

1. **Navigate to Scripts Directory**

   ```powershell
   cd docs\project\hours\scripts
   ```

2. **Verify Configuration**

   - Check `config.bat` contains correct paths:
     - `REPO_PARENT_DIR` - Parent directory containing repositories
     - `CSV_FILE` - Path to repositories.csv
     - `COMMITS_DIR` - Output directory for commit CSVs

3. **Run Git Commits Extraction**

   ```powershell
   .\extract_git_commits.ps1
   ```

4. **Verify Output**
   - Check log file: `docs\project\hours\data\git_extraction_log.txt`
   - Verify CSV files created in `docs\project\hours\data\commits\`
   - Each repository should have its own CSV file: `{repo_name}.csv`

#### Configuration

Edit `config.bat` to set:

```batch
set REPO_PARENT_DIR=C:\Users\piete\Repos\pkuppens
set CSV_FILE=%~dp0..\data\repositories.csv
set COMMITS_DIR=%~dp0..\data\commits
set GIT_LOG_OPTIONS=--date=iso --reverse --all
```

#### Output Format

Each repository produces a CSV file with columns:

- `datetime` - Commit timestamp (ISO format)
- `timestamp` - Unix timestamp
- `message` - Commit message
- `author` - Commit author name
- `hash` - Commit hash

#### Troubleshooting

**Issue: "Repository directory not found"**

- **Solution**: Verify repository is cloned to `REPO_PARENT_DIR`
- Check `repositories.csv` has correct repository names

**Issue: "CSV file not found"**

- **Solution**: Verify `repositories.csv` exists in data directory
- Check `config.bat` has correct path

**Issue: Git command fails**

- **Solution**: Verify Git is installed and in PATH
- Check repository is a valid Git repository
- Verify repository is not corrupted

**Issue: Some repositories fail**

- **Solution**: Check `git_extraction_log.txt` for specific errors
- Verify each repository is accessible and valid

## Automated Data Refresh

The pipeline can automatically execute data refresh when needed.

### How It Works

1. **Check Data Freshness**

   - Pipeline checks if data exists and is up-to-date (present until yesterday)
   - Compares latest file dates with current date

2. **Execute Refresh Subflows**

   - If data is stale, pipeline executes refresh subflows
   - Each subflow (system events, git commits) runs independently
   - Each subflow has its own error handling and bottlenecks

3. **Report Results**
   - Pipeline reports success/failure for each subflow
   - Continues with available data even if one subflow fails

### Enabling Automation

The pipeline automatically attempts data refresh when:

- `force_refresh=True` is set in context
- Data is detected as stale (older than yesterday)

### Subflow Bottlenecks

Each data refresh subflow has independent bottlenecks:

**System Events Bottleneck:**

- Requires Windows PowerShell
- Requires Administrator privileges for full access
- May fail if event logs are inaccessible

**Git Commits Bottleneck:**

- Requires Git installed
- Requires repositories to be cloned
- May fail for individual repositories without blocking others

## Best Practices

1. **Regular Refresh**

   - Run data refresh daily or before pipeline execution
   - System events should be refreshed at least weekly
   - Git commits should be refreshed daily

2. **Error Handling**

   - Check log files after manual execution
   - Verify output files contain expected data
   - Address errors before running pipeline

3. **Data Validation**

   - Verify CSV files are not empty
   - Check date ranges match expected periods
   - Validate file formats before pipeline execution

4. **Automation**
   - Use automated refresh when possible
   - Monitor subflow failures
   - Set up scheduled tasks for regular refresh

## Related Documentation

- [WBSO Data Flow](WBSO-DATA-FLOW.md) - Complete data flow documentation
- [System Events Format](data/SYSTEM_EVENTS_FORMAT.md) - System events CSV format
- [Extract-SystemEvents.ps1](scripts/Extract-SystemEvents.ps1) - System events extraction script
- [extract_git_commits.ps1](scripts/extract_git_commits.ps1) - Git commits extraction script

## Code Files

- [src/wbso/pipeline_steps.py](../../../src/wbso/pipeline_steps.py) - Pipeline steps including data refresh
- [docs/project/hours/scripts/Extract-SystemEvents.ps1](scripts/Extract-SystemEvents.ps1) - System events extraction script
- [docs/project/hours/scripts/extract_git_commits.ps1](scripts/extract_git_commits.ps1) - Git commits extraction script
