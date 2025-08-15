@echo off
setlocal enabledelayedexpansion

REM Test script to process a single repository
REM This script tests the git log extraction with one repository

echo ========================================
echo Single Repository Test Script
echo ========================================
echo.

REM Load shared configuration
call "%~dp0config.bat"

REM Load shared utilities
call "%~dp0utils.bat"

REM Create output directory if it doesn't exist
call :create_dir_if_not_exists "%COMMITS_DIR%"

REM Test with ai-agents-masterclass repository
set "repo_name=ai-agents-masterclass"
set "repo_path=%REPO_PARENT_DIR%\!repo_name!"

echo Testing repository: !repo_name!
echo Repository path: !repo_path!
echo.

if exist "!repo_path!" (
    echo Repository found. Processing...

    REM Change to repository directory
    pushd "!repo_path!"

    REM Create CSV file with header first
    set "header=datetime|timestamp|message|author|hash"
    echo !header! > "%COMMITS_DIR%\!repo_name!_test.csv"

    REM Extract git log data using separate script
    echo Extracting commit data...
    call "%~dp0git_log_extract.bat" "!repo_name!" "%COMMITS_DIR%\!repo_name!_test.csv"

    REM Check if git log was successful
    if !errorlevel! equ 0 (
        echo SUCCESS: Commit data extracted for !repo_name!
        echo Output file: %COMMITS_DIR%\!repo_name!_test.csv
    ) else (
        echo ERROR: Failed to extract commit data for !repo_name!
    )

    REM Return to original directory
    popd
) else (
    echo WARNING: Repository directory not found: !repo_path!
)

echo.
echo Test completed. Check the output file for results.
