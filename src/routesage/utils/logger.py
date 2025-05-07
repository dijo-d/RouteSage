"""
Logging configuration for RouteSage.

This module provides centralized logging setup and configuration
for the entire RouteSage application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure the RouteSage logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Optional custom format string for log messages

    Returns:
        Configured logger instance
    """
    global _logger

    # Create logger if not exists
    if _logger is None:
        _logger = logging.getLogger("routesage")
        _logger.setLevel(getattr(logging, level.upper()))

        # Default format
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)

    return _logger

def get_logger() -> logging.Logger:
    """
    Get the configured RouteSage logger.

    Returns:
        Logger instance
    
    Raises:
        RuntimeError: If logger hasn't been setup yet
    """
    if _logger is None:
        # Auto-initialize with default settings if not initialized
        return setup_logger()
    return _logger