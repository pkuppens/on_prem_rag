@echo off
setlocal enabledelayedexpansion

REM Extract Git Commit Data from Repositories
REM This script processes each repository in repositories.csv and extracts commit data

echo ========================================
echo Git Commit Data Extraction Script
echo ========================================
echo.

REM Load shared configuration
call "%~dp0config.bat"

REM Load shared utilities
call "%~dp0utils.bat"

REM Initialize log file
call :init_log "%LOG_FILE%" "Git Commit Extraction"

REM Check if repositories.csv exists
call :check_csv_exists "%CSV_FILE%"

REM Create output directory if it doesn't exist
call :create_dir_if_not_exists "%COMMITS_DIR%"

echo Processing repositories from: %CSV_FILE%
echo Output directory: %COMMITS_DIR%
echo Log file: %LOG_FILE%
echo Repository parent directory: %REPO_PARENT_DIR%
echo.

REM Read repositories.csv and process each repository
set "line_count=0"
set "processed_count=0"
set "error_count=0"

for /f "usebackq tokens=1,2 delims=," %%a in ("%CSV_FILE%") do (
    set /a line_count+=1

    REM Skip header line
    if !line_count! gtr 1 (
        REM Remove quotes from repo name and extract just the repo name (remove pkuppens/ prefix)
        set "repo_name=%%a"
        set "repo_name=!repo_name:"=!"

        REM Extract just the repository name (remove pkuppens/ prefix if present)
        for /f "tokens=2 delims=/" %%b in ("!repo_name!") do set "repo_name=%%b"

        REM Skip empty lines
        if not "!repo_name!"=="" (
            echo Processing repository: !repo_name!
            call :log_message "%LOG_FILE%" "Processing repository: !repo_name!"

            REM Check if repository directory exists in the correct location
            set "repo_path=%REPO_PARENT_DIR%\!repo_name!"
            if exist "!repo_path!" (
                REM Change to repository directory
                pushd "!repo_path!"

                REM Extract git log data
                echo Extracting commit data...

                REM Create CSV file with header first
                set "header=datetime|timestamp|message|author|hash"
                echo !header! > "%COMMITS_DIR%\!repo_name!.csv"

                REM Extract git log data with correct format and disable paging
                call "%~dp0git_log_extract.bat" "!repo_name!" "%COMMITS_DIR%\!repo_name!.csv"

                REM Check if git log was successful
                if !errorlevel! equ 0 (
                    echo SUCCESS: Commit data extracted for !repo_name!
                    call :log_message "%LOG_FILE%" "SUCCESS: Commit data extracted for !repo_name!"
                    set /a processed_count+=1
                ) else (
                    echo ERROR: Failed to extract commit data for !repo_name!
                    call :log_message "%LOG_FILE%" "ERROR: Failed to extract commit data for !repo_name!"
                    set /a error_count+=1
                )

                REM Return to original directory
                popd
            ) else (
                echo WARNING: Repository directory not found: !repo_path!
                call :log_message "%LOG_FILE%" "WARNING: Repository directory not found: !repo_path!"
                set /a error_count+=1
            )

            echo.
        )
    )
)

REM Summary
echo ========================================
echo EXTRACTION SUMMARY
echo ========================================
echo Total repositories processed: %processed_count%
echo Errors encountered: %error_count%
echo.
echo Output files created in: %COMMITS_DIR%
echo Detailed log: %LOG_FILE%
echo.

REM Write summary to log
call :log_message "%LOG_FILE%" "========================================"
call :log_message "%LOG_FILE%" "EXTRACTION SUMMARY"
call :log_message "%LOG_FILE%" "Total repositories processed: %processed_count%"
call :log_message "%LOG_FILE%" "Errors encountered: %error_count%"
call :log_message "%LOG_FILE%" "========================================"

if %error_count% gtr 0 (
    echo Some repositories could not be processed. Check the log file for details.
    echo.
) else (
    echo All repositories processed successfully!
    echo.
)
