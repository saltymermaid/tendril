import { apiFetch } from "../lib/api"
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface Settings {
  usda_zone: string
  weather_city: string | null
  weather_lat: number | null
  weather_lon: number | null
  has_claude_api_key: boolean
  session_timeout_hours: number
}

interface LocationResult {
  name: string
  region: string
  country_code: string
  display_name: string
  lat: number
  lon: number
}

const SESSION_TIMEOUT_OPTIONS = [
  { value: 4, label: '4 hours' },
  { value: 8, label: '8 hours' },
  { value: 24, label: '24 hours' },
  { value: 48, label: '48 hours' },
]

const USDA_ZONES = [
  '1a', '1b', '2a', '2b', '3a', '3b', '4a', '4b',
  '5a', '5b', '6a', '6b', '7a', '7b', '8a', '8b',
  '9a', '9b', '10a', '10b', '11a', '11b', '12a', '12b', '13a', '13b',
]

export function SettingsPage() {
  const { user } = useAuth()
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Form state
  const [usdaZone, setUsdaZone] = useState('10a')
  const [weatherCity, setWeatherCity] = useState('')
  const [weatherLat, setWeatherLat] = useState<number | null>(null)
  const [weatherLon, setWeatherLon] = useState<number | null>(null)
  const [claudeApiKey, setClaudeApiKey] = useState('')
  const [sessionTimeoutHours, setSessionTimeoutHours] = useState(4)

  // Location search state
  const [locationQuery, setLocationQuery] = useState('')
  const [locationResults, setLocationResults] = useState<LocationResult[]>([])
  const [locationSearching, setLocationSearching] = useState(false)
  const [showLocationDropdown, setShowLocationDropdown] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [gpsLoading, setGpsLoading] = useState(false)

  const searchWrapperRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    fetchSettings()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target as Node)) {
        setShowLocationDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced location search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (locationQuery.length < 2) {
      setLocationResults([])
      setShowLocationDropdown(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setLocationSearching(true)
      setLocationError(null)
      try {
        const res = await apiFetch(`/api/settings/location-search?q=${encodeURIComponent(locationQuery)}`)
        if (!res.ok) {
          setLocationError('Search failed — try again')
          return
        }
        const data: LocationResult[] = await res.json()
        setLocationResults(data)
        setShowLocationDropdown(data.length > 0)
      } catch {
        setLocationError('Search failed — check your connection')
      } finally {
        setLocationSearching(false)
      }
    }, 300)
  }, [locationQuery])

  const fetchSettings = async () => {
    try {
      const res = await apiFetch('/api/settings', { credentials: 'include' })
      if (res.ok) {
        const data: Settings = await res.json()
        setSettings(data)
        setUsdaZone(data.usda_zone)
        setWeatherCity(data.weather_city ?? '')
        setWeatherLat(data.weather_lat ?? null)
        setWeatherLon(data.weather_lon ?? null)
        setSessionTimeoutHours(data.session_timeout_hours ?? 4)
        // Pre-fill search field with current city if set
        if (data.weather_city) {
          setLocationQuery(data.weather_city)
        }
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to load settings' })
    } finally {
      setLoading(false)
    }
  }

  const handleLocationSelect = (result: LocationResult) => {
    setWeatherCity(result.display_name)
    setWeatherLat(result.lat)
    setWeatherLon(result.lon)
    setLocationQuery(result.display_name)
    setShowLocationDropdown(false)
    setLocationResults([])
    setLocationError(null)
  }

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser')
      return
    }
    setGpsLoading(true)
    setLocationError(null)
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        try {
          const res = await apiFetch(
            `/api/settings/reverse-geocode?lat=${latitude}&lon=${longitude}`
          )
          if (!res.ok) {
            setLocationError('Could not determine your location name')
            setGpsLoading(false)
            return
          }
          const data = await res.json()
          setWeatherCity(data.display_name)
          setWeatherLat(latitude)
          setWeatherLon(longitude)
          setLocationQuery(data.display_name)
          setShowLocationDropdown(false)
        } catch {
          setLocationError('Failed to look up your location — check your connection')
        } finally {
          setGpsLoading(false)
        }
      },
      (err) => {
        setGpsLoading(false)
        if (err.code === err.PERMISSION_DENIED) {
          setLocationError('Location access denied — please allow location in your browser settings')
        } else {
          setLocationError('Could not get your location')
        }
      },
      { timeout: 10000, maximumAge: 60000 }
    )
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)

    const body: Record<string, unknown> = {
      usda_zone: usdaZone,
      weather_city: weatherCity || null,
      session_timeout_hours: sessionTimeoutHours,
    }

    if (weatherLat !== null) body.weather_lat = weatherLat
    if (weatherLon !== null) body.weather_lon = weatherLon
    if (claudeApiKey) body.claude_api_key = claudeApiKey

    try {
      const res = await apiFetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      })

      if (res.ok) {
        const data: Settings = await res.json()
        setSettings(data)
        setClaudeApiKey('')
        setMessage({ type: 'success', text: 'Settings saved successfully!' })
        setTimeout(() => setMessage(null), 3000)
      } else {
        const err = await res.json().catch(() => ({ detail: 'Save failed' }))
        setMessage({ type: 'error', text: err.detail || 'Save failed' })
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="tendril-icon">🌱</div>
        <p>Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <h2>Settings</h2>
        <p className="text-muted">Configure your garden profile</p>
      </div>

      <form onSubmit={handleSubmit} className="settings-form">
        {/* USDA Zone */}
        <div className="form-group">
          <label htmlFor="usda-zone" className="form-label">USDA Hardiness Zone</label>
          <select
            id="usda-zone"
            value={usdaZone}
            onChange={(e) => setUsdaZone(e.target.value)}
            className="input"
          >
            {USDA_ZONES.map((zone) => (
              <option key={zone} value={zone}>
                Zone {zone}
              </option>
            ))}
          </select>
          <p className="form-help">Used to determine planting seasons for your area</p>
        </div>

        {/* Weather Location — smart search */}
        <div className="form-group">
          <label htmlFor="location-search" className="form-label">Weather Location</label>
          <div className="location-search-wrapper" ref={searchWrapperRef}>
            <div className="location-search-input-row">
              <input
                id="location-search"
                type="text"
                value={locationQuery}
                onChange={(e) => {
                  setLocationQuery(e.target.value)
                  // If user clears or modifies the field, clear the confirmed selection
                  if (e.target.value !== weatherCity) {
                    setWeatherCity('')
                    setWeatherLat(null)
                    setWeatherLon(null)
                  }
                  setLocationError(null)
                }}
                onFocus={() => {
                  if (locationResults.length > 0) setShowLocationDropdown(true)
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setShowLocationDropdown(false)
                }}
                placeholder="Search by city, state, or ZIP…"
                className="input"
                autoComplete="off"
                data-1p-ignore
                data-lpignore="true"
              />
              <button
                type="button"
                className={`btn btn-outline location-gps-btn${gpsLoading ? ' loading' : ''}`}
                onClick={handleUseMyLocation}
                disabled={gpsLoading}
                title="Use my current location"
              >
                {gpsLoading ? '…' : '📍'}
              </button>
            </div>

            {locationSearching && (
              <div className="location-search-dropdown">
                <div className="location-search-loading">Searching…</div>
              </div>
            )}

            {showLocationDropdown && !locationSearching && locationResults.length > 0 && (
              <ul className="location-search-dropdown" role="listbox">
                {locationResults.map((result, i) => (
                  <li
                    key={i}
                    className="location-search-item"
                    role="option"
                    onMouseDown={(e) => {
                      e.preventDefault() // prevent input blur before click registers
                      handleLocationSelect(result)
                    }}
                  >
                    <span className="location-search-item-name">{result.name}</span>
                    <span className="location-search-item-region text-muted">
                      {result.region}{result.region ? ', ' : ''}{result.country_code}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {locationError && <p className="form-error">{locationError}</p>}

          {weatherCity && weatherLat !== null && weatherLon !== null && (
            <p className="form-help location-confirmed">
              📍 {weatherCity}
              <span className="text-muted"> — {weatherLat.toFixed(4)}, {weatherLon.toFixed(4)}</span>
            </p>
          )}
          {!weatherCity && (
            <p className="form-help">
              Search for a city or tap 📍 to use your current location
            </p>
          )}
        </div>

        {/* Claude API Key */}
        <div className="form-group">
          <label htmlFor="claude-key" className="form-label">Claude API Key</label>
          <input
            id="claude-key"
            type="password"
            value={claudeApiKey}
            onChange={(e) => setClaudeApiKey(e.target.value)}
            placeholder={settings?.has_claude_api_key ? '••••••••••••••••' : 'sk-ant-...'}
            className="input"
          />
          <p className="form-help">
            {settings?.has_claude_api_key
              ? 'API key is saved. Enter a new value to replace it.'
              : 'Required for seed packet photo import (Phase 2)'}
          </p>
        </div>

        {/* Session Timeout */}
        <div className="form-group">
          <label className="form-label">Session Timeout</label>
          <div className="segmented-control">
            {SESSION_TIMEOUT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`segmented-btn${sessionTimeoutHours === opt.value ? ' active' : ''}`}
                onClick={() => setSessionTimeoutHours(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="form-help">How long you stay logged in. Takes effect on next login.</p>
        </div>

        {/* Account Info */}
        <div className="form-group">
          <label className="form-label">Account</label>
          <div className="account-info">
            <span>{user?.name}</span>
            <span className="text-muted">{user?.email}</span>
          </div>
        </div>

        {message && (
          <div className={`form-message ${message.type}`}>
            {message.text}
          </div>
        )}

        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </form>
    </div>
  )
}
