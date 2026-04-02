import { apiFetch } from "../lib/api"
import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'

interface ContainerFormData {
  name: string
  type: string
  location_description: string
  width: number | ''
  height: number | ''
  levels: number | ''
  pockets_per_level: number | ''
  irrigation_type: string
  irrigation_duration_minutes: number | ''
  irrigation_frequency: string
}

const EMPTY_FORM: ContainerFormData = {
  name: '',
  type: 'grid_bed',
  location_description: '',
  width: 4,
  height: 4,
  levels: '',
  pockets_per_level: '',
  irrigation_type: '',
  irrigation_duration_minutes: '',
  irrigation_frequency: '',
}

export function ContainerFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [form, setForm] = useState<ContainerFormData>({ ...EMPTY_FORM })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isEdit && id) fetchContainer()
  }, [id])

  async function fetchContainer() {
    try {
      const res = await apiFetch(`/api/containers/${id}`)
      if (!res.ok) throw new Error('Container not found')
      const data = await res.json()
      setForm({
        name: data.name,
        type: data.type,
        location_description: data.location_description || '',
        width: data.width ?? '',
        height: data.height ?? '',
        levels: data.levels ?? '',
        pockets_per_level: data.pockets_per_level ?? '',
        irrigation_type: data.irrigation_type || '',
        irrigation_duration_minutes: data.irrigation_duration_minutes ?? '',
        irrigation_frequency: data.irrigation_frequency || '',
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load container')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const body: Record<string, unknown> = {
        name: form.name,
        type: form.type,
        location_description: form.location_description || null,
        irrigation_type: form.irrigation_type || null,
        irrigation_duration_minutes: form.irrigation_duration_minutes || null,
        irrigation_frequency: form.irrigation_frequency || null,
      }

      if (form.type === 'grid_bed') {
        body.width = form.width || null
        body.height = form.height || null
        body.levels = null
        body.pockets_per_level = null
      } else {
        body.levels = form.levels || null
        body.pockets_per_level = form.pockets_per_level || null
        body.width = null
        body.height = null
      }

      const url = isEdit ? `/api/containers/${id}` : '/api/containers'
      const method = isEdit ? 'PUT' : 'POST'

      const res = await apiFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save container')
      }

      const saved = await res.json()
      navigate(`/containers/${saved.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save container')
    } finally {
      setSaving(false)
    }
  }

  function updateField(field: keyof ContainerFormData, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to={isEdit ? `/containers/${id}` : '/containers'} className="back-link">
          ← Back
        </Link>
        <h2>{isEdit ? 'Edit Container' : 'New Container'}</h2>
      </div>

      {error && <div className="form-message error">{error}</div>}

      <form onSubmit={handleSubmit} className="detail-form">
        <div className="form-card">
          <h3>Basic Information</h3>
          <div className="form-group">
            <label className="form-label">Name *</label>
            <input
              type="text"
              className="input"
              value={form.name}
              onChange={(e) => updateField('name', e.target.value)}
              required
              placeholder="e.g., Main Raised Bed"
            />
          </div>

          {!isEdit && (
            <div className="form-group">
              <label className="form-label">Type *</label>
              <div className="type-selector">
                <button
                  type="button"
                  className={`type-option ${form.type === 'grid_bed' ? 'active' : ''}`}
                  onClick={() => updateField('type', 'grid_bed')}
                >
                  <span className="type-icon">🌿</span>
                  <span>Garden Bed</span>
                  <span className="type-desc">Square-foot grid layout</span>
                </button>
                <button
                  type="button"
                  className={`type-option ${form.type === 'tower' ? 'active' : ''}`}
                  onClick={() => updateField('type', 'tower')}
                >
                  <span className="type-icon">🗼</span>
                  <span>Tower</span>
                  <span className="type-desc">Stacked levels with pockets</span>
                </button>
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Location</label>
            <input
              type="text"
              className="input"
              value={form.location_description}
              onChange={(e) => updateField('location_description', e.target.value)}
              placeholder="e.g., Backyard, south side"
            />
          </div>
        </div>

        {/* Dimensions */}
        <div className="form-card">
          <h3>{form.type === 'grid_bed' ? 'Grid Dimensions' : 'Tower Dimensions'}</h3>
          {form.type === 'grid_bed' ? (
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Width (columns) *</label>
                <input
                  type="number"
                  className="input"
                  value={form.width}
                  onChange={(e) => updateField('width', e.target.value ? parseInt(e.target.value) : '')}
                  min={1}
                  max={20}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Height (rows) *</label>
                <input
                  type="number"
                  className="input"
                  value={form.height}
                  onChange={(e) => updateField('height', e.target.value ? parseInt(e.target.value) : '')}
                  min={1}
                  max={20}
                  required
                />
              </div>
            </div>
          ) : (
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Number of Levels *</label>
                <input
                  type="number"
                  className="input"
                  value={form.levels}
                  onChange={(e) => updateField('levels', e.target.value ? parseInt(e.target.value) : '')}
                  min={1}
                  max={20}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Pockets per Level *</label>
                <input
                  type="number"
                  className="input"
                  value={form.pockets_per_level}
                  onChange={(e) => updateField('pockets_per_level', e.target.value ? parseInt(e.target.value) : '')}
                  min={1}
                  max={20}
                  required
                />
              </div>
            </div>
          )}
          {form.type === 'grid_bed' && form.width && form.height && (
            <p className="form-help">
              {Number(form.width) * Number(form.height)} total squares
            </p>
          )}
          {form.type === 'tower' && form.levels && form.pockets_per_level && (
            <p className="form-help">
              {Number(form.levels) * Number(form.pockets_per_level)} total pockets
            </p>
          )}
        </div>

        {/* Irrigation */}
        <div className="form-card">
          <h3>💧 Irrigation (optional)</h3>
          <div className="form-group">
            <label className="form-label">Irrigation Type</label>
            <select
              className="input"
              value={form.irrigation_type}
              onChange={(e) => updateField('irrigation_type', e.target.value)}
            >
              <option value="">None</option>
              <option value="drip">Drip</option>
              <option value="manual">Manual</option>
              <option value="sprinkler">Sprinkler</option>
            </select>
          </div>
          {form.irrigation_type && (
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Duration (minutes)</label>
                <input
                  type="number"
                  className="input"
                  value={form.irrigation_duration_minutes}
                  onChange={(e) => updateField('irrigation_duration_minutes', e.target.value ? parseInt(e.target.value) : '')}
                  min={1}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Frequency</label>
                <select
                  className="input"
                  value={form.irrigation_frequency}
                  onChange={(e) => updateField('irrigation_frequency', e.target.value)}
                >
                  <option value="">—</option>
                  <option value="daily">Daily</option>
                  <option value="2x_daily">Twice Daily</option>
                  <option value="every_2_days">Every 2 Days</option>
                  <option value="every_3_days">Every 3 Days</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : isEdit ? 'Update Container' : 'Create Container'}
          </button>
          <Link to={isEdit ? `/containers/${id}` : '/containers'} className="btn btn-outline-dark">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
