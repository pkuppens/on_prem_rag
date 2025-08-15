@echo off
REM Shared Utilities for WBSO Hours Project Scripts
REM This file contains common functions used by multiple scripts

REM Function: Initialize log file with header
:init_log
set "log_file=%~1"
set "script_name=%~2"
echo %script_name% Log - %date% %time% > "%log_file%"
echo ======================================== >> "%log_file%"
goto :eof

REM Function: Log message to file
:log_message
set "log_file=%~1"
set "message=%~2"
echo %message% >> "%log_file%"
goto :eof

REM Function: Check if CSV file exists
:check_csv_exists
set "csv_file=%~1"
if not exist "%csv_file%" (
    echo ERROR: CSV file not found: %csv_file%
    echo Please ensure repositories.csv exists in the data directory.
    pause
    exit /b 1
)
goto :eof

REM Function: Create directory if it doesn't exist
:create_dir_if_not_exists
set "dir_path=%~1"
if not exist "%dir_path%" (
    echo Creating directory: %dir_path%
    mkdir "%dir_path%"
)
goto :eof

REM Function: Remove quotes from string
:remove_quotes
set "input=%~1"
set "output=!input:"=!"
goto :eof

REM Function: Check if repository directory exists
:check_repo_exists
set "repo_name=%~1"
set "repo_path=%REPO_PARENT_DIR%\!repo_name!"
if exist "!repo_path!" (
    set "repo_exists=1"
) else (
    set "repo_exists=0"
)
goto :eof

REM Function: Change to repository directory
:change_to_repo
set "repo_name=%~1"
set "repo_path=%REPO_PARENT_DIR%\!repo_name!"
pushd "!repo_path!"
goto :eof

REM Function: Return to original directory
:return_from_repo
popd
goto :eof
