#!/usr/bin/env python3
"""
Run MCP Calendar Server Integration Test

This script runs the MCP calendar server integration test and generates a test report.
It can be used for regression testing - the diff will show when tests start failing or are fixed.

Usage:
    To run the integration test:
    
      1. Make sure the MCP Calendar server is running before executing the tests.
         If it is not running, start it in another terminal:
             uv run python src/mcp_calendar/server.py
    
      2. Then run the integration tests:
             uv run python tests/run_mcp_calendar_integration_test.py
    
    If the server is not started, all test cases will be SKIPPED.

Author: AI Assistant
Created: 2025-11-16
Updated: 2025-11-22
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import and run the test
import pytest

if __name__ == "__main__":
    # Run the integration tests (class-based tests)
    # The teardown fixture will automatically generate the test report
    exit_code = pytest.main([
        "tests/test_mcp_calendar_server.py::TestMCPCalendarServer",
        "-v",
        "-m", "internet",
        "--tb=short",
        "-s"
    ])
    
    sys.exit(exit_code)

