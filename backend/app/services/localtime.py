"""Helpers for interpreting naive reminder times in the garden's local timezone."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def to_utc(value: datetime | None) -> datetime | None:
    """Attach the app's local timezone to a naive datetime, then convert to UTC.

    A datetime that already carries a timezone is converted as-is. Used so a caller
    (a person, or Claude via MCP) can say "6pm tomorrow" without doing timezone math.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        local_tz = ZoneInfo(get_settings().app_timezone)
        value = value.replace(tzinfo=local_tz)
    return value
