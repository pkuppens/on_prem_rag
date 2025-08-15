@echo off
setlocal enabledelayedexpansion

REM Repository Management Script for WBSO Hours Project
REM This script reads repositories.csv and clones/updates all repositories

echo Repository Management Script - WBSO Hours Project
echo ================================================

REM Load shared configuration
call "%~dp0config.bat"

REM Load shared utilities
call "%~dp0utils.bat"

REM Initialize log file
call :init_log "%CLONE_LOG_FILE%" "Repository Management"

echo Parent Directory: %REPO_PARENT_DIR%
echo CSV File: %CSV_FILE%
echo Log File: %CLONE_LOG_FILE%
echo.

REM Check if parent directory exists
call :create_dir_if_not_exists "%REPO_PARENT_DIR%"

REM Change to parent directory
cd /d "%REPO_PARENT_DIR%"

REM Check if CSV file exists
call :check_csv_exists "%CSV_FILE%"

echo Starting repository processing...
call :log_message "%CLONE_LOG_FILE%" "Starting repository processing..."

REM Skip header line and process each repository
set /a line_count=0
for /f "usebackq tokens=1,2,3 delims=," %%a in ("%CSV_FILE%") do (
    set /a line_count+=1

    REM Skip header line
    if !line_count! gtr 1 (
        REM Remove quotes from repository name
        set repo_name=%%a
        set repo_name=!repo_name:"=!

        REM Skip empty lines
        if not "!repo_name!"=="" (
            echo Processing repository: !repo_name!
            call :log_message "%CLONE_LOG_FILE%" "Processing repository: !repo_name!"

            REM Convert repo name to GitHub URL
            set github_url=https://github.com/!repo_name!

            REM Check if directory already exists
            if exist "!repo_name!" (
                echo   Directory exists, updating...
                call :log_message "%CLONE_LOG_FILE%" "  Directory exists, updating..."
                cd /d "!repo_name!"
                git pull >> %CLONE_LOG_FILE% 2>&1
                if !errorlevel! equ 0 (
                    echo   ✓ Successfully updated
                    call :log_message "%CLONE_LOG_FILE%" "  ✓ Successfully updated"
                ) else (
                    echo   ✗ Failed to update
                    call :log_message "%CLONE_LOG_FILE%" "  ✗ Failed to update"
                )
                cd /d "%REPO_PARENT_DIR%"
            ) else (
                echo   Directory does not exist, cloning...
                call :log_message "%CLONE_LOG_FILE%" "  Directory does not exist, cloning..."
                git clone !github_url! >> %CLONE_LOG_FILE% 2>&1
                if !errorlevel! equ 0 (
                    echo   ✓ Successfully cloned
                    call :log_message "%CLONE_LOG_FILE%" "  ✓ Successfully cloned"
                ) else (
                    echo   ✗ Failed to clone
                    call :log_message "%CLONE_LOG_FILE%" "  ✗ Failed to clone"
                )
            )
            echo.
        )
    )
)

echo Repository processing complete!
call :log_message "%CLONE_LOG_FILE%" "Repository processing complete!"
echo.
echo Check the log file for details: %CLONE_LOG_FILE%
echo.
pause
