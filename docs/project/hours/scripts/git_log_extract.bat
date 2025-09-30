@echo off
REM Git Log Extraction Helper Script
REM This script extracts git log data with proper format escaping

set "repo_name=%~1"
set "output_file=%~2"

REM Extract git log data with correct format and disable paging
git --no-pager log --pretty=format:"%%ad|%%at|%%s|%%an|%%H" --date=iso --reverse --all >> "%output_file%" 2>&1
