@echo off
REM Test script to verify git log format
REM This script tests the git log format to ensure it works correctly

echo Testing git log format...
echo.

REM Test the format in the current directory (if it's a git repo)
if exist ".git" (
    echo Current directory is a git repository. Testing format:
    echo.
    echo "Expected format: datetime|timestamp|message|author|hash"
    echo.
    git --no-pager log --pretty=format:"%%ad|%%at|%%s|%%an|%%H" --date=format-local:%%Y-%%m-%%d %%H:%%M:%%S --reverse --all -n 3
    echo.
    echo Format test completed.
) else (
    echo Current directory is not a git repository.
    echo Please run this script from a git repository to test the format.
)

echo.
echo Test completed.
