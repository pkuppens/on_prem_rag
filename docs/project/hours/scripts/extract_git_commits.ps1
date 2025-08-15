# Extract Git Commit Data from Repositories
# This script processes each repository in repositories.csv and extracts commit data

param(
    [string]$ConfigFile = ".\config.bat"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git Commit Data Extraction Script (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load configuration from config.bat
$configContent = Get-Content $ConfigFile -Raw
$configLines = $configContent -split "`n"

# Parse configuration variables
$config = @{}
foreach ($line in $configLines) {
    if ($line -match '^set\s+(\w+)=(.*)$') {
        $key = $matches[1]
        $value = $matches[2].Trim()
        $config[$key] = $value
    }
}

# Set variables from config
$REPO_PARENT_DIR = $config['REPO_PARENT_DIR']
$CSV_FILE = $config['CSV_FILE']
$COMMITS_DIR = $config['COMMITS_DIR']
$LOG_FILE = $config['LOG_FILE']
$GIT_LOG_OPTIONS = $config['GIT_LOG_OPTIONS']

# Initialize log file
$logHeader = "Git Commit Extraction Log - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$logHeader | Out-File -FilePath $LOG_FILE -Encoding UTF8
"========================================" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8

# Check if repositories.csv exists
if (-not (Test-Path $CSV_FILE)) {
    Write-Host "ERROR: CSV file not found: $CSV_FILE" -ForegroundColor Red
    Write-Host "Please ensure repositories.csv exists in the data directory." -ForegroundColor Red
    exit 1
}

# Create output directory if it doesn't exist
if (-not (Test-Path $COMMITS_DIR)) {
    Write-Host "Creating directory: $COMMITS_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $COMMITS_DIR -Force | Out-Null
}

Write-Host "Processing repositories from: $CSV_FILE" -ForegroundColor Green
Write-Host "Output directory: $COMMITS_DIR" -ForegroundColor Green
Write-Host "Log file: $LOG_FILE" -ForegroundColor Green
Write-Host "Repository parent directory: $REPO_PARENT_DIR" -ForegroundColor Green
Write-Host ""

# Read CSV file
$repositories = Import-Csv -Path $CSV_FILE

$processedCount = 0
$errorCount = 0

foreach ($repo in $repositories) {
    $repoName = $repo.repo_name

    # Extract just the repository name (remove pkuppens/ prefix if present)
    if ($repoName -match '^[^/]+/(.+)$') {
        $repoName = $matches[1]
    }

    Write-Host "Processing repository: $repoName" -ForegroundColor Yellow
    "Processing repository: $repoName" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8

    # Check if repository directory exists
    $repoPath = Join-Path $REPO_PARENT_DIR $repoName
    if (Test-Path $repoPath) {
        Write-Host "Extracting commit data..." -ForegroundColor Gray

        # Create CSV file with header
        $outputFile = Join-Path $COMMITS_DIR "$repoName.csv"
        "datetime|timestamp|message|author|hash" | Out-File -FilePath $outputFile -Encoding UTF8

        # Change to repository directory
        Push-Location $repoPath

        try {
            # Extract git log data with correct format
            $gitCommand = "git --no-pager log --pretty=format:`"%ad|%at|%s|%an|%H`" $GIT_LOG_OPTIONS"
            $gitOutput = Invoke-Expression $gitCommand 2>&1

            if ($LASTEXITCODE -eq 0) {
                $gitOutput | Out-File -FilePath $outputFile -Append -Encoding UTF8
                Write-Host "SUCCESS: Commit data extracted for $repoName" -ForegroundColor Green
                "SUCCESS: Commit data extracted for $repoName" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
                $processedCount++
            } else {
                Write-Host "ERROR: Failed to extract commit data for $repoName" -ForegroundColor Red
                "ERROR: Failed to extract commit data for $repoName" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
                $errorCount++
            }
        }
        catch {
            Write-Host "ERROR: Exception occurred while processing $repoName : $_" -ForegroundColor Red
            "ERROR: Exception occurred while processing $repoName : $_" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
            $errorCount++
        }
        finally {
            # Return to original directory
            Pop-Location
        }
    } else {
        Write-Host "WARNING: Repository directory not found: $repoPath" -ForegroundColor Yellow
        "WARNING: Repository directory not found: $repoPath" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
        $errorCount++
    }

    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EXTRACTION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total repositories processed: $processedCount" -ForegroundColor Green
Write-Host "Errors encountered: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "Output files created in: $COMMITS_DIR" -ForegroundColor Green
Write-Host "Detailed log: $LOG_FILE" -ForegroundColor Green
Write-Host ""

# Write summary to log
"========================================" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
"EXTRACTION SUMMARY" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
"Total repositories processed: $processedCount" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
"Errors encountered: $errorCount" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
"========================================" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8

if ($errorCount -gt 0) {
    Write-Host "Some repositories could not be processed. Check the log file for details." -ForegroundColor Yellow
} else {
    Write-Host "All repositories processed successfully!" -ForegroundColor Green
}

Write-Host ""
