"""Minimal logging foundation conforming to Section 18 of Stage 1 specification.

Provides standard application logging with timestamps, log-level control,
service identification, and sensitive credential protection.
"""

from datetime import datetime, timezone
import logging
import sys
from typing import Any, Dict

# Credentials and secret patterns that must never be logged
SENSITIVE_PATTERNS = (
    "password",
    "secret",
    "token",
    "key",
    "authorization",
    "credential",
)


class SafeFormatter(logging.Formatter):
    """Log formatter ensuring timestamp, service identification, and secret masking."""

    def __init__(self, service_name: str = "ADDMAI-API") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        message = record.getMessage()

        # Mask potential secrets if present in log message
        for pattern in SENSITIVE_PATTERNS:
            if pattern in message.lower() and "=" in message:
                message = "[REDACTED SENSITIVE LOG ENTRY]"
                break

        return f"[{timestamp}] [{record.levelname:<7}] [{self.service_name}] [{record.name}]: {message}"


def setup_logging(service_name: str = "ADDMAI-API", log_level: str = "INFO") -> None:
    """Initialize application logging with standard handlers."""
    root_logger = logging.getLogger()
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(SafeFormatter(service_name=service_name))
    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    """Return configured logger instance."""
    return logging.getLogger(name)
