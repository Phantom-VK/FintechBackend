"""Structured logging configuration for the application."""

from datetime import datetime
import logging
from pathlib import Path
import sys

import structlog


BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BASE_DIR / "logs"


def build_log_file_path() -> Path:
    """Return a timestamped log file path for the current app start."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOGS_DIR / f"app_{timestamp}.log"


def setup_logging() -> Path:
    """Configure JSON logging with request-scoped context."""

    LOGS_DIR.mkdir(exist_ok=True)
    log_file_path = build_log_file_path()

    logging.basicConfig(
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file_path, encoding="utf-8"),
        ],
        level=logging.INFO,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return log_file_path
