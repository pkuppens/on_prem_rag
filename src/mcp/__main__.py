#!/usr/bin/env python3
"""
MCP Calendar Server Entry Point

This module allows running the MCP calendar server as a module:
    python -m mcp.calendar_server

Author: AI Assistant
Created: 2025-11-15
"""

import asyncio

from mcp.calendar_server import main

if __name__ == "__main__":
    asyncio.run(main())
