"""
C-SWON Logging Utilities

Provides the setup_events_logger function used by the config module
for structured event logging.
"""

import logging
from logging.handlers import RotatingFileHandler
import os


def setup_events_logger(full_path: str, events_retention_size: int) -> logging.Logger:
    """
    Set up a dedicated events logger with rotating file handler.

    Args:
        full_path: Directory path where event log files will be written.
        events_retention_size: Maximum size of each log file in bytes before rotation.

    Returns:
        A configured Logger instance for events.
    """
    logger = logging.getLogger("events")
    logger.setLevel(logging.DEBUG)

    log_file = os.path.join(full_path, "events.log")

    # Ensure the directory exists
    os.makedirs(full_path, exist_ok=True)

    # Rotating file handler with size-based rotation
    handler = RotatingFileHandler(
        log_file,
        maxBytes=int(events_retention_size) if events_retention_size else 2 * 1024 * 1024 * 1024,
        backupCount=3,
    )
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.addHandler(handler)

    return logger
