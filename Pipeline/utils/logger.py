"""
Production logger.
Features
--------
- No duplicate handlers
- Console + file logging
- Thread-safe
- Singleton logger
"""

from pathlib import Path
import logging
from config import LOG_DIR
LOG_FILE = Path(LOG_DIR) / "prepare_dataset.log"

def _create_logger():
    logger = logging.getLogger(
        "prepare_dataset"
    )
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(
        formatter
    )

    file = logging.FileHandler(
        LOG_FILE,
        encoding="utf8"
    )

    file.setFormatter(
        formatter
    )

    logger.addHandler(console)
    logger.addHandler(file)
    logger.propagate = False
    return logger


logger = _create_logger()

def info(message):
    logger.info(message)

def warning(message):
    logger.warning(message)

def error(message):
    logger.error(message)

def debug(message):
    logger.debug(message)

def exception(message):
    logger.exception(message)