#!/usr/bin/env python3
"""Test script to verify the improved logging format."""

from backend.rag_pipeline.utils.logging import StructuredLogger


def test_function():
    """Test function to demonstrate logging."""
    logger = StructuredLogger("test_logger", level="DEBUG")

    logger.info("This is an info message", extra_data="test_value")
    logger.debug("This is a debug message", debug_data="debug_value")
    logger.warning("This is a warning message", warning_data="warning_value")
    logger.error("This is an error message", error_data="error_value")


if __name__ == "__main__":
    test_function()
