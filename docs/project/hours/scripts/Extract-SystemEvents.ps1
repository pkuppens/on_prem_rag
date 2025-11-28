# Windows System Events Extractor
# Extracts system startup/shutdown and user logon/logoff events to CSV
# Author: Generated for system activity tracking
# Date: 2025

param(
    [Parameter(Mandatory = $false)]
    [DateTime]$StartDate = (Get-Date "2025-01-01"),

    [Parameter(Mandatory = $false)]
    [DateTime]$EndDate = (Get-Date),

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ""
)

# Set default output path to data directory if not provided
if ([string]::IsNullOrEmpty($OutputPath)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $dataDir = Join-Path $scriptDir "..\data"
    $dataDir = [System.IO.Path]::GetFullPath($dataDir)
    $dateStr = Get-Date -Format 'yyyyMMdd'
    $OutputPath = Join-Path $dataDir "system_events_$dateStr.csv"
}

Write-Host "Extracting Windows events from $StartDate to $EndDate"
Write-Host "Output file: $OutputPath"

# Define event IDs and their meanings
$EventDefinitions = @{
    # System Events (System Log)
    6005 = @{Log = "System"; Description = "System startup (Event Log service started)" }
    6006 = @{Log = "System"; Description = "System shutdown (Event Log service stopped)" }
    6008 = @{Log = "System"; Description = "Unexpected shutdown (previous shutdown was unexpected)" }
    1074 = @{Log = "System"; Description = "System shutdown/restart initiated" }
    41   = @{Log = "System"; Description = "System rebooted without cleanly shutting down" }
    6013 = @{Log = "System"; Description = "System uptime report" }

    # Security Events (Security Log) - Logon/Logoff
    4624 = @{Log = "Security"; Description = "Successful logon" }
    4625 = @{Log = "Security"; Description = "Failed logon attempt" }
    4634 = @{Log = "Security"; Description = "Account logoff" }
    4647 = @{Log = "Security"; Description = "User initiated logoff" }
    4648 = @{Log = "Security"; Description = "Logon using explicit credentials" }

    # Power events
    42   = @{Log = "System"; Description = "System entering sleep" }
    # 1 = @{Log="System"; Description="System resumed from sleep"}  # Too many events - commented out

    # User logon/logoff notifications (required for computer-on detection)
    7001 = @{Log = "System"; Description = "User logon notification" }
    7002 = @{Log = "System"; Description = "User logoff notification" }

    # Additional potentially interesting events (commented out for now):
    # 4800 = @{Log="Security"; Description="Workstation locked"}
    # 4801 = @{Log="Security"; Description="Workstation unlocked"}
    # 4802 = @{Log="Security"; Description="Screen saver invoked"}
    # 4803 = @{Log="Security"; Description="Screen saver dismissed"}
    # 104 = @{Log="System"; Description="Event log cleared"}
    # 6009 = @{Log="System"; Description="System processor information at startup"}
    # 12 = @{Log="System"; Description="Operating system started"}
    # 13 = @{Log="System"; Description="Operating system shutdown"}
    # 4608 = @{Log="Security"; Description="Windows is starting up"}
    # 4609 = @{Log="Security"; Description="Windows is shutting down"}
    # 4616 = @{Log="Security"; Description="System time was changed"}
    # 4902 = @{Log="Security"; Description="Per-user audit policy table created"}
    # 4904 = @{Log="Security"; Description="An attempt was made to register a security event source"}
    # 5152 = @{Log="Security"; Description="Windows Filtering Platform blocked a packet"}  # Network activity
    # 5156 = @{Log="Security"; Description="Windows Filtering Platform allowed a connection"}  # Network activity
}

# Initialize results array
$AllEvents = @()

Write-Host "Collecting events..."

# Process each event type
foreach ($EventId in $EventDefinitions.Keys) {
    $LogName = $EventDefinitions[$EventId].Log
    $Description = $EventDefinitions[$EventId].Description

    Write-Host "Processing Event ID $EventId from $LogName log..."

    try {
        $Events = Get-WinEvent -FilterHashtable @{
            LogName   = $LogName
            Id        = $EventId
            StartTime = $StartDate
            EndTime   = $EndDate
        } -ErrorAction SilentlyContinue

        foreach ($Event in $Events) {
            # Extract additional details based on event type
            $AdditionalInfo = ""
            $Username = ""
            $ProcessName = ""

            # Parse XML for more details
            try {
                [xml]$EventXML = $Event.ToXml()

                # Extract common fields
                if ($EventXML.Event.EventData.Data) {
                    $EventData = @{}
                    foreach ($Data in $EventXML.Event.EventData.Data) {
                        if ($Data.Name) {
                            $EventData[$Data.Name] = $Data.'#text'
                        }
                    }

                    # Event-specific parsing
                    switch ($EventId) {
                        1074 {
                            $Username = $EventData.SubjectUserName
                            $ProcessName = $EventData.Process
                            $AdditionalInfo = "Reason: $($EventData.Reason), Comment: $($EventData.Comment)"
                        }
                        4624 {
                            $Username = $EventData.TargetUserName
                            $AdditionalInfo = "Logon Type: $($EventData.LogonType), Workstation: $($EventData.WorkstationName)"
                        }
                        4634 {
                            $Username = $EventData.TargetUserName
                            $AdditionalInfo = "Logon Type: $($EventData.LogonType)"
                        }
                        4647 {
                            $Username = $EventData.TargetUserName
                        }
                        Default {
                            if ($EventData.SubjectUserName) { $Username = $EventData.SubjectUserName }
                            if ($EventData.TargetUserName) { $Username = $EventData.TargetUserName }
                        }
                    }
                }
            }
            catch {
                # If XML parsing fails, continue with basic info
            }

            # Create event object
            $EventObj = [PSCustomObject]@{
                DateTime       = $Event.TimeCreated.ToString("yyyy/MM/dd HH:mm:ss")
                EventId        = $Event.Id
                LogName        = $Event.LogName
                EventType      = $Description
                Level          = $Event.LevelDisplayName
                Username       = if ($Username) { $Username } else { "N/A" }
                ProcessName    = if ($ProcessName) { $ProcessName } else { "N/A" }
                Message        = ($Event.Message -replace "`r`n", " " -replace "`n", " ").Trim()
                AdditionalInfo = $AdditionalInfo
                RecordId       = $Event.RecordId
            }

            $AllEvents += $EventObj
        }

        Write-Host "  Found $($Events.Count) events for Event ID $EventId"
    }
    catch {
        Write-Host "  No events found for Event ID $EventId in $LogName log (or access denied)"
    }
}

# Sort events by date
Write-Host "Sorting events by date..."
$AllEvents = $AllEvents | Sort-Object DateTime

# Export to CSV
Write-Host "Exporting $($AllEvents.Count) events to CSV..."
$AllEvents | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

Write-Host "Done! Events exported to: $OutputPath"
Write-Host "Total events found: $($AllEvents.Count)"

# Display summary statistics
Write-Host "`nEvent Summary:"
$AllEvents | Group-Object EventId | Sort-Object Count -Descending | ForEach-Object {
    $EventDesc = $EventDefinitions[$_.Name].Description
    Write-Host "  Event $($_.Name): $($_.Count) occurrences ($EventDesc)"
}

Write-Host "`nDate Range: $($AllEvents[0].DateTime) to $($AllEvents[-1].DateTime)"
