# WBSO Calendar Integration Test Runner for PowerShell
# This script provides an easy way to run the WBSO calendar tests

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WBSO Calendar Integration Test Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.12+ and ensure it's in your PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if uv is available
try {
    $uvVersion = uv --version 2>&1
    Write-Host "uv detected: $uvVersion" -ForegroundColor Green
    Write-Host ""
    Write-Host "Running tests with uv..." -ForegroundColor Yellow
    uv run test_wbso_calendar_integration.py
} catch {
    Write-Host "WARNING: uv is not available, using python directly" -ForegroundColor Yellow
    Write-Host "For better dependency management, install uv: https://docs.astral.sh/uv/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Running tests with python..." -ForegroundColor Yellow
    python test_wbso_calendar_integration.py
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test execution completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the following files for results:" -ForegroundColor White
Write-Host "- wbso_calendar_test_report.md" -ForegroundColor Gray
Write-Host "- wbso_calendar_test_results.json" -ForegroundColor Gray
Write-Host "- wbso_calendar_test.log" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"
