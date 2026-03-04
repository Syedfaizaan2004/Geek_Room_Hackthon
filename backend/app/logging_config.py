"""
logging_config.py — Centralised structured logging setup.

Call setup_logging() once at application startup (in main.py lifespan).
All other modules should simply use: logger = logging.getLogger(__name__)
"""

import logging
import sys
from pythonjsonlogger import json as jsonlogger  # type: ignore


def setup_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """
    Configure the root logger.

    Args:
        log_level:   Logging level string (DEBUG / INFO / WARNING / ERROR).
        json_output: When True, emit JSON lines (preferred in production / Render).
                     When False, emit human-readable output (development).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate log lines
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_output:
        # Structured JSON logs — ideal for log-aggregation tools (Render, GCP, etc.)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        # Human-readable format for local development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Confirm logging is ready
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging initialised",
        extra={"log_level": log_level, "json_mode": json_output},
    )


def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper — equivalent to logging.getLogger(name).
    Usage: logger = get_logger(__name__)
    """
    return logging.getLogger(name)
