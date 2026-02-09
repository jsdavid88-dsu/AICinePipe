"""
Logging configuration for AIPipeline Master Server.

Uses loguru for structured logging with rotation and consistent formatting.
"""

import sys
import os
from loguru import logger

from .config import settings


def setup_logging() -> None:
    """Configure loguru with console and file sinks."""
    # Remove default handler
    logger.remove()

    log_level = settings.LOG_LEVEL.upper()

    # Console sink
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
    )

    # File sink with rotation
    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "server.log")

    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )


# Run setup on import
setup_logging()


def get_logger(name: str = None):
    """
    Get a contextualized logger.

    Args:
        name: Module name for context (e.g., "worker", "api")

    Returns:
        Bound loguru logger
    """
    if name:
        return logger.bind(name=name)
    return logger
