"""Weather service — fetches 7-day forecast from Open-Meteo API with caching."""

import time
from dataclasses import dataclass, field

import httpx

# Open-Meteo WMO weather codes → description + emoji
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Heavy freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Slight snow", "🌨️"),
    73: ("Moderate snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "🌨️"),
    80: ("Slight showers", "🌦️"),
    81: ("Moderate showers", "🌧️"),
    82: ("Violent showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

# Default location: St. Petersburg, FL (USDA Zone 10a)
DEFAULT_LAT = 27.7676
DEFAULT_LON = -82.6403

# Cache TTL: 1 hour
CACHE_TTL_SECONDS = 3600


@dataclass
class DayForecast:
    """Single day forecast."""
    date: str
    weather_code: int
    weather_description: str
    weather_icon: str
    temperature_max: float
    temperature_min: float
    precipitation_probability_max: int
    sunrise: str
    sunset: str


@dataclass
class WeatherCache:
    """Simple in-memory cache for weather data."""
    data: dict | None = None
    timestamp: float = 0.0
    cache_key: str = ""


# Module-level cache
_cache = WeatherCache()


async def fetch_weather(lat: float | None, lon: float | None) -> list[DayForecast]:
    """Fetch 7-day weather forecast from Open-Meteo API.

    Uses in-memory caching with 1-hour TTL to avoid excessive API calls.
    Falls back to St. Petersburg, FL defaults if no location configured.
    """
    global _cache

    use_lat = lat if lat is not None else DEFAULT_LAT
    use_lon = lon if lon is not None else DEFAULT_LON
    cache_key = f"{use_lat:.4f},{use_lon:.4f}"

    # Check cache
    now = time.time()
    if (
        _cache.data is not None
        and _cache.cache_key == cache_key
        and (now - _cache.timestamp) < CACHE_TTL_SECONDS
    ):
        return _parse_forecast(_cache.data)

    # Fetch from Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": use_lat,
        "longitude": use_lon,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "sunrise",
            "sunset",
        ]),
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "forecast_days": 7,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    # Update cache
    _cache.data = data
    _cache.timestamp = now
    _cache.cache_key = cache_key

    return _parse_forecast(data)


def _parse_forecast(data: dict) -> list[DayForecast]:
    """Parse Open-Meteo API response into DayForecast objects."""
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    temp_maxes = daily.get("temperature_2m_max", [])
    temp_mins = daily.get("temperature_2m_min", [])
    precip_probs = daily.get("precipitation_probability_max", [])
    sunrises = daily.get("sunrise", [])
    sunsets = daily.get("sunset", [])

    forecasts = []
    for i in range(len(dates)):
        code = weather_codes[i] if i < len(weather_codes) else 0
        desc, icon = WMO_CODES.get(code, ("Unknown", "❓"))
        forecasts.append(DayForecast(
            date=dates[i],
            weather_code=code,
            weather_description=desc,
            weather_icon=icon,
            temperature_max=round(temp_maxes[i], 1) if i < len(temp_maxes) else 0,
            temperature_min=round(temp_mins[i], 1) if i < len(temp_mins) else 0,
            precipitation_probability_max=precip_probs[i] if i < len(precip_probs) else 0,
            sunrise=sunrises[i] if i < len(sunrises) else "",
            sunset=sunsets[i] if i < len(sunsets) else "",
        ))

    return forecasts
