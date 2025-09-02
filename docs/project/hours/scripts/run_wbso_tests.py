#!/usr/bin/env python3
"""
Simple test runner for WBSO calendar integration tests.

This script provides a convenient way to run the comprehensive WBSO calendar
integration tests with proper error handling and output formatting.
"""

import sys
from pathlib import Path

# Add the scripts directory to the Python path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

try:
    from test_wbso_calendar_integration import main
except ImportError as e:
    print(f"Error importing test module: {e}")
    print("Please ensure test_wbso_calendar_integration.py is in the same directory")
    sys.exit(1)

if __name__ == "__main__":
    print("WBSO Calendar Integration Test Runner")
    print("=" * 50)

    try:
        # Run the main test function
        main()
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during test execution: {e}")
        sys.exit(1)
