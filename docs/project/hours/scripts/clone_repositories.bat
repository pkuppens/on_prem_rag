@echo off
REM Repository Management Script for WBSO Hours Project
REM This script reads repositories.csv and clones/updates all repositories

setlocal enabledelayedexpansion

REM Set the repository parent directory
set REPO_PARENT_DIR=C:\Users\piete\Repos\pkuppens
set CSV_FILE=%~dp0..\data\repositories.csv
set LOG_FILE=%~dp0..\data\clone_log.txt

echo Repository Management Script - WBSO Hours Project
echo ================================================
echo Parent Directory: %REPO_PARENT_DIR%
echo CSV File: %CSV_FILE%
echo Log File: %LOG_FILE%
echo.

REM Create log file header
echo Repository Management Log - %date% %time% > %LOG_FILE%
echo ================================================ >> %LOG_FILE%

REM Check if parent directory exists
if not exist "%REPO_PARENT_DIR%" (
    echo Creating parent directory: %REPO_PARENT_DIR%
    mkdir "%REPO_PARENT_DIR%"
)

REM Change to parent directory
cd /d "%REPO_PARENT_DIR%"

REM Check if CSV file exists
if not exist "%CSV_FILE%" (
    echo ERROR: CSV file not found: %CSV_FILE%
    echo ERROR: CSV file not found: %CSV_FILE% >> %LOG_FILE%
    pause
    exit /b 1
)

echo Starting repository processing...
echo Starting repository processing... >> %LOG_FILE%

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
            echo Processing repository: !repo_name! >> %LOG_FILE%

            REM Convert repo name to GitHub URL
            set github_url=https://github.com/!repo_name!

            REM Check if directory already exists
            if exist "!repo_name!" (
                echo   Directory exists, updating...
                echo   Directory exists, updating... >> %LOG_FILE%
                cd /d "!repo_name!"
                git pull >> %LOG_FILE% 2>&1
                if !errorlevel! equ 0 (
                    echo   ✓ Successfully updated
                    echo   ✓ Successfully updated >> %LOG_FILE%
                ) else (
                    echo   ✗ Failed to update
                    echo   ✗ Failed to update >> %LOG_FILE%
                )
                cd /d "%REPO_PARENT_DIR%"
            ) else (
                echo   Directory does not exist, cloning...
                echo   Directory does not exist, cloning... >> %LOG_FILE%
                git clone !github_url! >> %LOG_FILE% 2>&1
                if !errorlevel! equ 0 (
                    echo   ✓ Successfully cloned
                    echo   ✓ Successfully cloned >> %LOG_FILE%
                ) else (
                    echo   ✗ Failed to clone
                    echo   ✗ Failed to clone >> %LOG_FILE%
                )
            )
            echo.
        )
    )
)

echo Repository processing complete!
echo Repository processing complete! >> %LOG_FILE%
echo.
echo Check the log file for details: %LOG_FILE%
echo.
pause
