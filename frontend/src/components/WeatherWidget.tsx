import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface DayForecast {
  date: string
  weather_code: number
  weather_description: string
  weather_icon: string
  temperature_max: number
  temperature_min: number
  precipitation_probability_max: number
  sunrise: string
  sunset: string
}

interface WeatherData {
  forecast: DayForecast[]
  location_configured: boolean
  city_name: string | null
}

function formatDayName(dateStr: string, index: number): string {
  if (index === 0) return 'Today'
  if (index === 1) return 'Tomorrow'
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-US', { weekday: 'short' })
}

function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function WeatherWidget() {
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchWeather() {
      try {
        const res = await fetch('/api/weather')
        if (!res.ok) {
          throw new Error('Weather unavailable')
        }
        const data = await res.json()
        setWeather(data)
      } catch (err) {
        setError('Weather unavailable')
      } finally {
        setLoading(false)
      }
    }
    fetchWeather()
  }, [])

  if (loading) {
    return (
      <div className="weather-widget">
        <div className="weather-header">
          <h3>🌤️ Weather</h3>
        </div>
        <div className="weather-loading">Loading forecast…</div>
      </div>
    )
  }

  if (error || !weather) {
    return (
      <div className="weather-widget">
        <div className="weather-header">
          <h3>🌤️ Weather</h3>
        </div>
        <div className="weather-error">
          <p>Unable to load weather data.</p>
          <p className="text-secondary">Check your connection and try again.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="weather-widget">
      <div className="weather-header">
        <div className="weather-header-title">
          <h3>🌤️ 7-Day Forecast</h3>
          {weather.city_name && (
            <span className="weather-city-name">📍 {weather.city_name}</span>
          )}
        </div>
        {!weather.location_configured && (
          <Link to="/settings" className="weather-config-link">
            📍 Set location
          </Link>
        )}
      </div>

      <div className="weather-forecast">
        {weather.forecast.map((day, i) => (
          <div
            key={day.date}
            className={`weather-day ${i === 0 ? 'weather-day-today' : ''}`}
          >
            <div className="weather-day-name">{formatDayName(day.date, i)}</div>
            <div className="weather-day-date">{formatShortDate(day.date)}</div>
            <div className="weather-day-icon" title={day.weather_description}>
              {day.weather_icon}
            </div>
            <div className="weather-day-temps">
              <span className="weather-temp-high">{Math.round(day.temperature_max)}°</span>
              <span className="weather-temp-low">{Math.round(day.temperature_min)}°</span>
            </div>
            {day.precipitation_probability_max > 0 && (
              <div className="weather-day-rain">
                💧 {day.precipitation_probability_max}%
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
