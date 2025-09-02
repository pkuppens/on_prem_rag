@echo off
REM WBSO Calendar Integration Test Runner for Windows
REM This batch file provides an easy way to run the WBSO calendar tests

echo.
echo ========================================
echo WBSO Calendar Integration Test Runner
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12+ and ensure it's in your PATH
    pause
    exit /b 1
)

REM Check if uv is available
uv --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: uv is not available, using python directly
    echo For better dependency management, install uv: https://docs.astral.sh/uv/
    echo.
    echo Running tests with python...
    python test_wbso_calendar_integration.py
) else (
    echo uv detected - using uv for dependency management
    echo.
    echo Running tests with uv...
    uv run test_wbso_calendar_integration.py
)

echo.
echo ========================================
echo Test execution completed
echo ========================================
echo.
echo Check the following files for results:
echo - wbso_calendar_test_report.md
echo - wbso_calendar_test_results.json
echo - wbso_calendar_test.log
echo.
pause
