"""Centralized logging configuration with structured formatting and security filters."""

import logging
import re
import sys

# Masking patterns for sensitive financial/identity data
SENSITIVE_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "***-**-****"),  # SSN
    (re.compile(r"(?i)(password|secret|api_key|token|auth_token)\s*=\s*['\"]?[^\s'\"]+"), r"\1=***REDACTED***"),
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]+"), r"\1***REDACTED***"),
]


class SensitiveDataFilter(logging.Filter):
    """Logging filter to redact sensitive information such as SSNs, passwords, and API keys."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in SENSITIVE_PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        return True


def setup_logging(log_level: str | None = "INFO") -> None:
    """Initialize structured logging configuration."""
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)

    log_format = (
        "%(asctime)s [%(levelname)s] [%(name)s] "
        "[%(filename)s:%(lineno)d] - %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S"))
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup is called multiple times
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Obtain a named logger instance."""
    return logging.getLogger(name)
