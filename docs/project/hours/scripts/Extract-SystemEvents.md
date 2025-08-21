## How to Use the Script

**1. Run the PowerShell script** (requires Administrator privileges for Security log access):

```powershell
# Basic usage (extracts from Jan 1, 2025 to now)
.\Extract-SystemEvents.ps1

# Custom date range
.\Extract-SystemEvents.ps1 -StartDate "2025-01-01" -EndDate "2025-08-21"

# Custom output location
.\Extract-SystemEvents.ps1 -OutputPath "C:\temp\my_system_events.csv"
```

**2. Grant necessary permissions:**

- Run PowerShell as Administrator (needed for Security log access)
- You may need to adjust execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## What You'll Get

The CSV will contain these **key event types**:

- **6005/6006**: System startup/shutdown (most reliable power state tracking)
- **1074**: User-initiated shutdowns/restarts (captures planned shutdowns)
- **4624/4634/4647**: User logon/logoff events
- **41**: Unexpected shutdowns (crashes, power loss)
- **6008**: Boot after unexpected shutdown

## Expected Volume

Based on typical usage (boot once, login/logout a few times daily), you should see:

- **System events**: 2-6 per day (startup, shutdown, maybe sleep/wake)
- **Security events**: 4-10 per day (multiple logon/logoff sessions)
- **Total**: 10-20 events per day typically, easily manageable for year-long analysis

## For Python Processing

The CSV structure is Python-friendly. You'll be able to:

- Calculate session durations by pairing logon/logoff events
- Track total system uptime by pairing startup/shutdown events
- Handle missing events (system crashes, etc.)
- Generate daily/weekly usage summaries

The **RecordId** field helps identify potentially missing events (gaps in sequence), and the **AdditionalInfo** field contains parsed details that might be useful for filtering or analysis.

Would you like me to also create a basic Python script template for processing this CSV data?
