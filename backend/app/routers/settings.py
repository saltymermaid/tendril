"""User settings router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _settings_to_response(settings: dict) -> SettingsResponse:
    """Convert user settings JSONB to response schema."""
    return SettingsResponse(
        usda_zone=settings.get("usda_zone", "10a"),
        weather_zip_code=settings.get("weather_zip_code", ""),
        weather_lat=settings.get("weather_lat"),
        weather_lon=settings.get("weather_lon"),
        has_claude_api_key=bool(settings.get("claude_api_key")),
    )


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
):
    """Return the current user's settings."""
    return _settings_to_response(current_user.settings or {})


@router.put("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's settings."""
    settings = dict(current_user.settings or {})

    # Only update fields that were explicitly provided
    update_data = body.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "claude_api_key":
            # Only update if a non-empty value is provided
            if value:
                settings["claude_api_key"] = value
            # If empty string, clear the key
            elif value == "":
                settings.pop("claude_api_key", None)
            # If None (not provided), skip
        else:
            if value is not None:
                settings[key] = value

    current_user.settings = settings
    await db.flush()

    return _settings_to_response(settings)
