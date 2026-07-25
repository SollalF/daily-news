"""
Logging configuration for the application.
Provides a consistent logging interface for all modules.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from settings import settings

# Define log levels
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# ANSI color codes
COLORS = {
    "RESET": "\033[0m",
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BOLD": "\033[1m",
}

# Colors for each log level
LEVEL_COLORS = {
    "DEBUG": COLORS["BLUE"],
    "INFO": COLORS["GREEN"],
    "WARNING": COLORS["YELLOW"],
    "ERROR": COLORS["RED"],
    "CRITICAL": COLORS["BOLD"] + COLORS["RED"],
}


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to log level names."""

    def format(self, record):
        """Format the log record with colored level name."""
        # Save the original levelname
        levelname = record.levelname

        # Add color to the levelname
        if levelname in LEVEL_COLORS:
            record.levelname = f"{LEVEL_COLORS[levelname]}{levelname}{COLORS['RESET']}"

        # Call the original formatter
        result = super().format(record)

        # Restore the original levelname
        record.levelname = levelname

        return result


# Initialize the logger
logger = logging.getLogger("daily-news")


def setup_logger(
    log_level: str | None = None,
    log_file: str | None = None,
    log_format: str | None = None,
    max_file_size: int | None = None,
    backup_count: int | None = None,
) -> logging.Logger:
    """
    Configure the application logger.

    Args:
        log_level: Logging level (debug, info, warning, error, critical)
        log_file: Path to log file (if None, logs only to console)
        log_format: Format string for log messages
        max_file_size: Maximum size of log file before rotation (in bytes)
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Use settings values or provided parameters
    level = log_level or settings.logging.level
    file_path = log_file or settings.logging.log_file
    format_str = log_format or settings.logging.format
    file_size = max_file_size or settings.logging.max_file_size
    backups = backup_count or settings.logging.backup_count

    # Set log level
    level_value = LOG_LEVELS.get(level.lower(), logging.INFO)
    logger.setLevel(level_value)

    # Create formatters
    console_formatter = ColoredFormatter(format_str)
    # Use a more detailed format for log files
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file is specified)
    if file_path:
        log_path = Path(file_path)
        # Ensure the directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path, maxBytes=file_size, backupCount=backups
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Initialize with default settings
setup_logger()
