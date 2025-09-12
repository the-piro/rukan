"""Simple logging configuration for MEGA downloader bot."""

import logging
import sys
from .config import Config


def setup_logger() -> logging.Logger:
    """Setup and configure logger."""
    logger = logging.getLogger("mega_bot")

    if logger.handlers:
        return logger

    # Set log level
    level = logging.DEBUG if Config.DEBUG else logging.INFO
    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


# Global logger instance
LOGGER = setup_logger()
