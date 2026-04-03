"""User settings Pydantic schemas."""

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    """User settings returned from GET /api/settings."""
    usda_zone: str
    weather_city: str | None
    weather_lat: float | None
    weather_lon: float | None
    has_claude_api_key: bool  # Never return the actual key
    session_timeout_hours: int  # Default 4, max 48


class SettingsUpdate(BaseModel):
    """Request body for PUT /api/settings."""
    usda_zone: str | None = None
    weather_city: str | None = None
    weather_lat: float | None = None
    weather_lon: float | None = None
    claude_api_key: str | None = None  # Only set when user provides a new key
    session_timeout_hours: int | None = None  # 4, 8, 24, or 48
