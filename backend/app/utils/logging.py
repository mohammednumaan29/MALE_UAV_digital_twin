"""
Structured Logging Utility for Rotax 914 Digital Twin Backend.
Configures formatted console and file logging.
"""

import logging
import sys
from app.config.settings import settings


def setup_logging() -> logging.Logger:
    """Configure and return the root application logger."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    logger = logging.getLogger("rotax914_twin")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        logger.addHandler(handler)
        
    logger.propagate = False
    return logger


logger = setup_logging()
