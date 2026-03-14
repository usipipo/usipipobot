"""
Logger configuration for uSipipo VPN Android APK.
"""

import os
import sys

from loguru import logger
from src.config import APP_DATA_DIR


def setup_logger(log_level: str = "DEBUG") -> None:
    """
    Configure logger for both console and file output.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Ensure log directory exists
    log_dir = os.path.join(APP_DATA_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler with color
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Add file handler (rotating)
    logger.add(
        os.path.join(log_dir, "usipipo_apk.log"),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 MB",
        retention="7 days",
        compression="zip",
    )

    logger.info("Logger configured successfully")


# Auto-setup when module is imported
setup_logger()
