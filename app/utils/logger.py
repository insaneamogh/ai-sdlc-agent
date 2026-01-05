#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
Logger Utility Module

This module provides a configured logger using loguru for consistent
logging across the application.
"""

import sys
from loguru import logger
from app.config import get_settings


def setup_logger():
    """
    Configure the logger with appropriate settings.
    
    Sets up:
    - Console output with colors
    - Log level from settings
    - Consistent format across the application
    """
    settings = get_settings()
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )
    
    # Add file handler for production (optional)
    if not settings.debug:
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="INFO"
        )
    
    return logger


# Initialize logger on module import
# This ensures the logger is configured when imported
try:
    setup_logger()
except Exception:
    # If settings fail to load, use default logger
    pass


# Export the configured logger
__all__ = ["logger"]

#__________________________GenAI: Generated code ends here______________________________#
