import logging
import re
import sys
from core.config import settings


class SecretMaskingFilter(logging.Filter):
    """
    Filter that inspects log record messages and masks sensitive information
    such as passwords, tokens, JWT secret keys, and API keys before output.
    """

    PATTERNS = [
        (re.compile(r'(password["\':\s=]+)([^\s,`\'"]+)', re.IGNORECASE), r'\1***MASKED***'),
        (re.compile(r'(access_token["\':\s=]+)([^\s,`\'"]+)', re.IGNORECASE), r'\1***MASKED***'),
        (re.compile(r'(Bearer\s+)([A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*)', re.IGNORECASE), r'\1***MASKED_TOKEN***'),
        (re.compile(r'(api_key["\':\s=]+)([^\s,`\'"]+)', re.IGNORECASE), r'\1***MASKED***'),
        (re.compile(r'(secret["\':\s=]+)([^\s,`\'"]+)', re.IGNORECASE), r'\1***MASKED***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def setup_logger(name: str = "CampusMind") -> logging.Logger:
    """
    Sets up a structured console logger with secret masking and level controls.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        handler.addFilter(SecretMaskingFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()
