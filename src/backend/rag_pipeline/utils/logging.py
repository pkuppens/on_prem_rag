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


class CallerAwareFormatter(logging.Formatter):
    """Custom formatter that shows caller information instead of logging function location.

    This formatter extracts the actual caller information from the log record
    and formats it as a clickable link with complete path and line number.
    """

    def format(self, record):
        # Extract caller info from the log message if it's in our format
        if hasattr(record, "caller_info"):
            caller_info = record.caller_info
            # Format as clickable link: filename:line (function)
            caller_str = f"{caller_info['filename']}:{caller_info['line']} ({caller_info['function']})"
            record.caller = caller_str
        else:
            # Fallback to standard format if no caller info
            record.caller = f"{record.filename}:{record.lineno} ({record.funcName})"

        return super().format(record)


class StructuredLogger:
    """A structured logger that includes caller information and supports JSON formatting.

    This logger enhances Python's standard logging with:
    - Automatic inclusion of caller information (file, function, line)
    - JSON-formatted log messages for better parsing
    - Consistent log format across the application
    - Clickable links in debug output showing complete file paths

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

        # Create console handler with custom formatting
        handler = logging.StreamHandler(sys.stdout)
        formatter = CallerAwareFormatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(caller)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _get_caller_info(self) -> dict[str, Any]:
        """Get information about the calling function.

        Returns:
            Dict containing filename, function name, and line number
        """
        # Go back 3 frames: 1 for _log_with_caller_info, 1 for the logging method, 1 for the caller
        frame = inspect.currentframe().f_back.f_back.f_back

        # Get the full path and make it relative to the current working directory
        full_path = Path(frame.f_code.co_filename)
        try:
            relative_path = full_path.relative_to(Path.cwd())
        except ValueError:
            # If not relative to current directory, use the full path
            relative_path = full_path

        return {"filename": str(relative_path), "function": frame.f_code.co_name, "line": frame.f_lineno}

    def _log_with_caller_info(self, level: int, message: str, **kwargs) -> None:
        """Internal method to log with caller information.

        Args:
            level: The logging level
            message: The log message
            **kwargs: Additional structured data to include
        """
        caller = self._get_caller_info()

        # Create a custom log record with caller info
        record = self.logger.makeRecord(
            self.logger.name, level, caller["filename"], caller["line"], message, (), None, caller["function"]
        )

        # Add caller info to the record
        record.caller_info = caller

        # Add additional structured data to the message
        if kwargs:
            structured_data = {**caller, **kwargs}
            record.msg = f"{message} | {json.dumps(structured_data)}"
        else:
            record.msg = f"{message} | {json.dumps(caller)}"

        self.logger.handle(record)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        self._log_with_caller_info(logging.INFO, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        self._log_with_caller_info(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        self._log_with_caller_info(logging.DEBUG, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message with structured data.

        Args:
            message: The log message
            **kwargs: Additional structured data to include
        """
        self._log_with_caller_info(logging.WARNING, message, **kwargs)
