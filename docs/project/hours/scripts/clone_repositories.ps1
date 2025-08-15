# Repository Management Script for WBSO Hours Project
# This script reads repositories.csv and clones/updates all repositories

param(
    [string]$RepoParentDir = "C:\Users\piete\Repos\pkuppens",
    [string]$CsvFile = "$PSScriptRoot\..\data\repositories.csv",
    [string]$LogFile = "$PSScriptRoot\..\data\clone_log.txt"
)

# Function to write to both console and log file
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

# Initialize log file
$logHeader = @"
Repository Management Log - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
================================================
"@
Set-Content -Path $LogFile -Value $logHeader

Write-Log "Repository Management Script - WBSO Hours Project"
Write-Log "================================================"
Write-Log "Parent Directory: $RepoParentDir"
Write-Log "CSV File: $CsvFile"
Write-Log "Log File: $LogFile"
Write-Log ""

# Check if parent directory exists
if (-not (Test-Path $RepoParentDir)) {
    Write-Log "Creating parent directory: $RepoParentDir"
    New-Item -ItemType Directory -Path $RepoParentDir -Force | Out-Null
}

# Check if CSV file exists
if (-not (Test-Path $CsvFile)) {
    Write-Log "ERROR: CSV file not found: $CsvFile" "ERROR"
    exit 1
}

# Change to parent directory
Set-Location $RepoParentDir
Write-Log "Changed to directory: $(Get-Location)"

# Read CSV file
try {
    $repositories = Import-Csv -Path $CsvFile
    Write-Log "Successfully loaded $($repositories.Count) repositories from CSV"
} catch {
    Write-Log "ERROR: Failed to read CSV file: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Log "Starting repository processing..."

$successCount = 0
$failureCount = 0

foreach ($repo in $repositories) {
    $repoName = $repo.repo_name
    $githubUrl = "https://github.com/$repoName"

    Write-Log "Processing repository: $repoName"

    # Check if directory already exists
    if (Test-Path $repoName) {
        Write-Log "  Directory exists, updating..."
        Set-Location $repoName

        try {
            $pullResult = git pull 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "  ✓ Successfully updated" "SUCCESS"
                $successCount++
            } else {
                Write-Log "  ✗ Failed to update: $pullResult" "ERROR"
                $failureCount++
            }
        } catch {
            Write-Log "  ✗ Exception during update: $($_.Exception.Message)" "ERROR"
            $failureCount++
        }

        Set-Location $RepoParentDir
    } else {
        Write-Log "  Directory does not exist, cloning..."

        try {
            $cloneResult = git clone $githubUrl 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "  ✓ Successfully cloned" "SUCCESS"
                $successCount++
            } else {
                Write-Log "  ✗ Failed to clone: $cloneResult" "ERROR"
                $failureCount++
            }
        } catch {
            Write-Log "  ✗ Exception during clone: $($_.Exception.Message)" "ERROR"
            $failureCount++
        }
    }

    Write-Log ""
}

Write-Log "Repository processing complete!"
Write-Log "Summary: $successCount successful, $failureCount failed"
Write-Log ""
Write-Log "Check the log file for details: $LogFile"

# Create a summary report
$summaryReport = @"
Repository Management Summary
============================
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Total Repositories: $($repositories.Count)
Successful Operations: $successCount
Failed Operations: $failureCount
Success Rate: $([math]::Round(($successCount / $repositories.Count) * 100, 2))%

Failed Repositories:
"@

if ($failureCount -gt 0) {
    # This would need to be enhanced to track which specific repos failed
    $summaryReport += "`n(Check log file for details)"
}

Add-Content -Path $LogFile -Value "`n$summaryReport"
Write-Log "Summary report added to log file"
