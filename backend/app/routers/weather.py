"""Weather router — 7-day forecast from Open-Meteo API."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.services.weather import fetch_weather

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weather", tags=["weather"])


class DayForecastResponse(BaseModel):
    date: str
    weather_code: int
    weather_description: str
    weather_icon: str
    temperature_max: float
    temperature_min: float
    precipitation_probability_max: int
    sunrise: str
    sunset: str


class WeatherResponse(BaseModel):
    forecast: list[DayForecastResponse]
    location_configured: bool


@router.get("", response_model=WeatherResponse)
async def get_weather(
    current_user: User = Depends(get_current_user),
):
    """Get 7-day weather forecast for the user's configured location."""
    settings = current_user.settings or {}
    lat = settings.get("weather_lat")
    lon = settings.get("weather_lon")
    location_configured = lat is not None and lon is not None

    try:
        forecasts = await fetch_weather(lat, lon)
        return WeatherResponse(
            forecast=[
                DayForecastResponse(
                    date=f.date,
                    weather_code=f.weather_code,
                    weather_description=f.weather_description,
                    weather_icon=f.weather_icon,
                    temperature_max=f.temperature_max,
                    temperature_min=f.temperature_min,
                    precipitation_probability_max=f.precipitation_probability_max,
                    sunrise=f.sunrise,
                    sunset=f.sunset,
                )
                for f in forecasts
            ],
            location_configured=location_configured,
        )
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch weather data. Please try again later.",
        )
