#!/usr/bin/env python3
"""
Wrapper module for test_mcp_calendar_client script.

This module allows the script to be used as an entry point while maintaining
the script in the scripts/ directory.

Author: AI Assistant
Created: 2025-11-15
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import main_sync from the scripts directory
import importlib.util

spec = importlib.util.spec_from_file_location("test_mcp_calendar_client_script", scripts_dir / "test_mcp_calendar_client.py")
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)
main_sync = test_module.main_sync

__all__ = ["main_sync"]
