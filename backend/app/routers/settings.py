"""User settings router."""

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class LocationSearchResult(BaseModel):
    name: str
    region: str
    country_code: str
    display_name: str
    lat: float
    lon: float


class ReverseGeocodeResponse(BaseModel):
    display_name: str
    lat: float
    lon: float


@router.get("/location-search", response_model=list[LocationSearchResult])
async def location_search(
    q: str = Query(..., min_length=2, max_length=100),
    current_user: User = Depends(get_current_user),
):
    """Search for locations by city name, state, or ZIP using Open-Meteo Geocoding API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": q, "count": 5, "language": "en", "format": "json"},
            )
        res.raise_for_status()
        data = res.json()
        results = data.get("results", [])
        out = []
        for r in results:
            name = r.get("name", "")
            region = r.get("admin1") or r.get("country", "")
            country_code = r.get("country_code", "")
            country = r.get("country", "")
            # Build a human-readable display name
            parts = [name]
            if region and region != name:
                parts.append(region)
            if country and country not in parts:
                parts.append(country)
            display_name = ", ".join(parts)
            out.append(LocationSearchResult(
                name=name,
                region=region,
                country_code=country_code,
                display_name=display_name,
                lat=float(r.get("latitude", 0)),
                lon=float(r.get("longitude", 0)),
            ))
        return out
    except Exception as e:
        logger.error(f"Location search error: {e}")
        raise HTTPException(status_code=502, detail="Location search failed")


@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(
    lat: float = Query(...),
    lon: float = Query(...),
    current_user: User = Depends(get_current_user),
):
    """Reverse geocode lat/lon to a city name using Nominatim (OpenStreetMap)."""
    try:
        async with httpx.AsyncClient(timeout=5.0, headers={"User-Agent": "Tendril/1.0"}) as client:
            res = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lon, "format": "json"},
            )
        res.raise_for_status()
        data = res.json()
        addr = data.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", "")
        state = addr.get("state", "")
        country = addr.get("country", "")
        parts = [p for p in [city, state, country] if p]
        display_name = ", ".join(parts) if parts else data.get("display_name", "Unknown location")
        return ReverseGeocodeResponse(display_name=display_name, lat=lat, lon=lon)
    except Exception as e:
        logger.error(f"Reverse geocode error: {e}")
        raise HTTPException(status_code=502, detail="Reverse geocode failed")


def _settings_to_response(settings: dict) -> SettingsResponse:
    """Convert user settings JSONB to response schema."""
    return SettingsResponse(
        usda_zone=settings.get("usda_zone", "10a"),
        weather_city=settings.get("weather_city") or None,
        weather_lat=settings.get("weather_lat"),
        weather_lon=settings.get("weather_lon"),
        has_claude_api_key=bool(settings.get("claude_api_key")),
        session_timeout_hours=settings.get("session_timeout_hours", 4),
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

    VALID_SESSION_TIMEOUTS = {4, 8, 24, 48}

    for key, value in update_data.items():
        if key == "claude_api_key":
            # Only update if a non-empty value is provided
            if value:
                settings["claude_api_key"] = value
            # If empty string, clear the key
            elif value == "":
                settings.pop("claude_api_key", None)
            # If None (not provided), skip
        elif key == "session_timeout_hours":
            if value in VALID_SESSION_TIMEOUTS:
                settings["session_timeout_hours"] = value
        else:
            if value is not None:
                settings[key] = value

    current_user.settings = settings
    await db.flush()

    return _settings_to_response(settings)
