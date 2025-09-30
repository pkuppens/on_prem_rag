@echo off
REM Shared Configuration for WBSO Hours Project Scripts
REM This file contains common variables and settings used by multiple scripts

REM Repository and Data Paths
set REPO_PARENT_DIR=C:\Users\piete\Repos\pkuppens
set CSV_FILE=%~dp0..\data\repositories.csv
set COMMITS_DIR=%~dp0..\data\commits
set LOG_FILE=%~dp0..\data\git_extraction_log.txt
set CLONE_LOG_FILE=%~dp0..\data\clone_log.txt

REM Script Settings
set SCRIPT_NAME=%~n0
set SCRIPT_VERSION=1.0

REM Git Settings
set GIT_LOG_OPTIONS=--date=iso --reverse --all

REM Display Configuration
echo Configuration loaded:
echo   Repository Parent: %REPO_PARENT_DIR%
echo   CSV File: %CSV_FILE%
echo   Commits Directory: %COMMITS_DIR%
echo   Log File: %LOG_FILE%
echo.
