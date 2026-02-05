"""
Logging Configuration for AIPipeline Master Server.

Provides structured logging with rotation and consistent formatting.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str = "aipipeline",
    log_dir: str = None,
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Sets up a logger with both console and file handlers.
    
    Args:
        name: Logger name
        log_dir: Directory for log files (defaults to project root)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (with rotation)
    if log_dir is None:
        log_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    log_file = os.path.join(log_dir, "server.log")
    
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler: {e}")
    
    return logger


# Singleton logger instance
logger = setup_logger()


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a child logger with the given name.
    
    Args:
        name: Optional child logger name (e.g., "worker", "api")
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"aipipeline.{name}")
    return logger
