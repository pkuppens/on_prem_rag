"""
Centralized logging configuration for WBSO module.

This module provides a centralized logging configuration that can be used
across all WBSO scripts and modules to ensure consistent logging behavior.

TASK-039: WBSO Calendar Data Validation, Upload, and Reporting System
Story: STORY-008 (WBSO Hours Registration System)
Epic: EPIC-002 (WBSO Compliance and Documentation)
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO, log_file: Path = None) -> logging.Logger:
    """
    Set up centralized logging configuration for WBSO module.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    # Create formatter
    formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Get root logger
    logger = logging.getLogger("wbso")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the WBSO module.

    Args:
        name: Optional logger name (defaults to 'wbso')

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"wbso.{name}")
    return logging.getLogger("wbso")


# Initialize default logging configuration
setup_logging()
