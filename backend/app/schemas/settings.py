"""User settings Pydantic schemas."""

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    """User settings returned from GET /api/settings."""
    usda_zone: str
    weather_zip_code: str
    weather_lat: float | None
    weather_lon: float | None
    has_claude_api_key: bool  # Never return the actual key


class SettingsUpdate(BaseModel):
    """Request body for PUT /api/settings."""
    usda_zone: str | None = None
    weather_zip_code: str | None = None
    weather_lat: float | None = None
    weather_lon: float | None = None
    claude_api_key: str | None = None  # Only set when user provides a new key
