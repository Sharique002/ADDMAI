"""Minimal logging foundation conforming to Section 15 of Stage 1.1 specification.

Provides standard application logging with UTC timestamps, log-level control,
service identification, and automatic redaction of passwords, API keys,
secret values, and database connection credentials.
"""

from datetime import datetime, timezone
import logging
import re
import sys
from typing import List

# Patterns containing sensitive keys
SENSITIVE_PATTERNS: List[str] = [
    "password",
    "secret",
    "token",
    "api_key",
    "access_key",
    "secret_key",
    "authorization",
    "credential",
]

# Regex to redact passwords in database connection URIs (e.g., postgresql://user:pass@host)
URI_PASSWORD_REGEX = re.compile(r"(://[^:\s]+):([^@\s]+)@")


class SafeFormatter(logging.Formatter):
    """Log formatter ensuring UTC timestamp, service tags, and sensitive credential masking."""

    def __init__(self, service_name: str = "ADDMAI-API") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        message = record.getMessage()

        # 1. Redact credentials embedded in connection URIs
        message = URI_PASSWORD_REGEX.sub(r"\1:[REDACTED]@", message)

        # 2. Redact key-value secrets (e.g. password=xyz or secret_key: xyz)
        for pattern in SENSITIVE_PATTERNS:
            regex_kv = re.compile(rf"(?i)({pattern}\s*[=:]\s*)(['\"]?[^\s,'\"]+['\"]?)")
            message = regex_kv.sub(r"\1[REDACTED]", message)

        return f"[{timestamp}] [{record.levelname:<7}] [{self.service_name}] [{record.name}]: {message}"


def setup_logging(service_name: str = "ADDMAI-API", log_level: str = "INFO") -> None:
    """Initialize application logging with standard handlers."""
    root_logger = logging.getLogger()
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Clear existing handlers to prevent duplicate lines
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(SafeFormatter(service_name=service_name))
    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    """Return configured logger instance."""
    return logging.getLogger(name)
