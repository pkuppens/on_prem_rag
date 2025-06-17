"""Structured logging utilities for the RAG pipeline.

This module provides a structured logging implementation that includes
caller information and supports JSON-formatted log messages.
"""

import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any


class StructuredLogger:
    """A structured logger that includes caller information and supports JSON formatting.

    This logger enhances Python's standard logging with:
    - Automatic inclusion of caller information (file, function, line)
    - JSON-formatted log messages for better parsing
    - Consistent log format across the application

    Attributes:
        logger: The underlying Python logger instance
        level: The current logging level
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """Initialize the structured logger.

        Args:
            name: The name of the logger
            level: The logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.level = level

        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _get_caller_info(self) -> dict[str, Any]:
        """Get information about the calling function.

        Returns:
            Dict containing filename, function name, and line number
        """
        frame = inspect.currentframe().f_back.f_back
        return {"filename": Path(frame.f_code.co_filename).name, "function": frame.f_code.co_name, "line": frame.f_lineno}

    def info(self, message: str, **kwargs) -> None:
        """Log an info message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        caller = self._get_caller_info()
        self.logger.info(f"{message} | {json.dumps({**caller, **kwargs})}")

    def error(self, message: str, **kwargs) -> None:
        """Log an error message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        caller = self._get_caller_info()
        self.logger.error(f"{message} | {json.dumps({**caller, **kwargs})}")

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        caller = self._get_caller_info()
        self.logger.debug(f"{message} | {json.dumps({**caller, **kwargs})}")

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        caller = self._get_caller_info()
        self.logger.warning(f"{message} | {json.dumps({**caller, **kwargs})}")
