import { useEffect, useState, type FormEvent } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface Settings {
  usda_zone: string
  weather_zip_code: string
  weather_lat: number | null
  weather_lon: number | null
  has_claude_api_key: boolean
}

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
  const [weatherZip, setWeatherZip] = useState('')
  const [weatherLat, setWeatherLat] = useState('')
  const [weatherLon, setWeatherLon] = useState('')
  const [claudeApiKey, setClaudeApiKey] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings', { credentials: 'include' })
      if (res.ok) {
        const data: Settings = await res.json()
        setSettings(data)
        setUsdaZone(data.usda_zone)
        setWeatherZip(data.weather_zip_code)
        setWeatherLat(data.weather_lat?.toString() ?? '')
        setWeatherLon(data.weather_lon?.toString() ?? '')
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to load settings' })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)

    const body: Record<string, unknown> = {
      usda_zone: usdaZone,
      weather_zip_code: weatherZip,
    }

    if (weatherLat) body.weather_lat = parseFloat(weatherLat)
    if (weatherLon) body.weather_lon = parseFloat(weatherLon)
    if (claudeApiKey) body.claude_api_key = claudeApiKey

    try {
      const res = await fetch('/api/settings', {
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

        {/* Weather Location */}
        <div className="form-group">
          <label htmlFor="weather-zip" className="form-label">Weather ZIP Code</label>
          <input
            id="weather-zip"
            type="text"
            value={weatherZip}
            onChange={(e) => setWeatherZip(e.target.value)}
            placeholder="33701"
            className="input"
            maxLength={10}
          />
          <p className="form-help">For weather display on the dashboard</p>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="weather-lat" className="form-label">Latitude</label>
            <input
              id="weather-lat"
              type="number"
              step="any"
              value={weatherLat}
              onChange={(e) => setWeatherLat(e.target.value)}
              placeholder="27.7676"
              className="input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="weather-lon" className="form-label">Longitude</label>
            <input
              id="weather-lon"
              type="number"
              step="any"
              value={weatherLon}
              onChange={(e) => setWeatherLon(e.target.value)}
              placeholder="-82.6403"
              className="input"
            />
          </div>
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
