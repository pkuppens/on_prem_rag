#!/usr/bin/env python3
"""
Standalone script to start the MCP Calendar Server

This script provides a convenient way to start the MCP calendar server
with various configuration options.

Usage:
    python scripts/start_mcp_calendar_server.py [--transport stdio|http] [--port PORT] [--credentials-path PATH] [--token-path PATH]

Author: AI Assistant
Created: 2025-11-15
"""

import argparse
import asyncio
import os
import sys

from mcp.calendar_server import main


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start MCP Calendar Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port (only used with --transport http, default: 8000)",
    )
    parser.add_argument(
        "--credentials-path",
        type=str,
        help="Path to Google OAuth credentials JSON file",
    )
    parser.add_argument(
        "--token-path",
        type=str,
        help="Path to Google OAuth token JSON file",
    )

    return parser.parse_args()


def main_cli():
    """Main CLI entry point."""
    args = parse_arguments()

    # Set environment variables if provided
    if args.credentials_path:
        os.environ["GOOGLE_CREDENTIALS_PATH"] = args.credentials_path
    if args.token_path:
        os.environ["GOOGLE_TOKEN_PATH"] = args.token_path

    print("Starting MCP Calendar Server...")
    print(f"Transport: {args.transport}")
    if args.transport == "http":
        print(f"Port: {args.port}")
        print("Note: HTTP transport is not yet implemented, using stdio")
    print()

    # Run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()

