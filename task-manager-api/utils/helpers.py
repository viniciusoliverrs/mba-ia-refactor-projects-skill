from datetime import datetime, timezone
import logging
import re
import uuid

from config.constants import (
    DEFAULT_COLOR,
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
)

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def utcnow():
    """Retorna datetime UTC naive compatível com colunas DateTime do SQLite sem usar datetime.utcnow() deprecated."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_date(date_obj):
    return str(date_obj) if date_obj else None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return isinstance(email, str) and bool(EMAIL_PATTERN.match(email))


def sanitize_string(value):
    return value.strip() if isinstance(value, str) else value


def generate_id():
    return str(uuid.uuid4())


def log_action(action, details=None):
    logger.info("ACTION: %s | DETAILS: %s", action, details)


def parse_date(date_string):
    if not isinstance(date_string, str):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None


def is_valid_color(color):
    return isinstance(color, str) and len(color) == 7 and color.startswith("#")


def serialize_tags(tags):
    if isinstance(tags, list):
        return ",".join(str(tag) for tag in tags)
    return str(tags) if tags else None


__all__ = [
    "DEFAULT_COLOR",
    "DEFAULT_PRIORITY",
    "MAX_PRIORITY",
    "MAX_TITLE_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "MIN_PRIORITY",
    "MIN_TITLE_LENGTH",
    "VALID_ROLES",
    "VALID_STATUSES",
    "calculate_percentage",
    "format_date",
    "generate_id",
    "is_valid_color",
    "log_action",
    "parse_date",
    "sanitize_string",
    "serialize_tags",
    "utcnow",
    "validate_email",
]
