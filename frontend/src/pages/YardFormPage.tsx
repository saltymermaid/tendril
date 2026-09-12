import { apiFetch } from "../lib/api"
import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'

interface YardFormData {
  name: string
  width: number | ''
  height: number | ''
}

const EMPTY_FORM: YardFormData = {
  name: '',
  width: 10,
  height: 10,
}

export function YardFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [form, setForm] = useState<YardFormData>({ ...EMPTY_FORM })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isEdit && id) fetchYard()
  }, [id])

  async function fetchYard() {
    try {
      const res = await apiFetch(`/api/yards/${id}`)
      if (!res.ok) throw new Error('Yard not found')
      const data = await res.json()
      setForm({ name: data.name, width: data.width, height: data.height })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load yard')
    } finally {
      setLoading(false)
    }
  }

  function updateField(field: keyof YardFormData, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const body = {
        name: form.name,
        width: form.width || null,
        height: form.height || null,
      }

      const url = isEdit ? `/api/yards/${id}` : '/api/yards'
      const method = isEdit ? 'PUT' : 'POST'

      const res = await apiFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save yard')
      }

      const saved = await res.json()
      navigate(`/yards/${saved.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save yard')
    } finally {
      setSaving(false)
    }
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
        <Link to={isEdit ? `/yards/${id}` : '/yards'} className="back-link">
          ← Back
        </Link>
        <h2>{isEdit ? 'Edit Yard' : 'New Yard'}</h2>
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
              placeholder="e.g., North Yard"
            />
          </div>
        </div>

        <div className="form-card">
          <h3>Grid Dimensions</h3>
          <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
            Same square-foot units as your garden beds — a 4×4 bed takes up a 4×4 block here.
          </p>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Width (columns) *</label>
              <input
                type="number"
                className="input"
                value={form.width}
                onChange={(e) => updateField('width', e.target.value ? parseInt(e.target.value) : '')}
                min={1}
                max={100}
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
                max={100}
                required
              />
            </div>
          </div>
          {form.width && form.height && (
            <p className="form-help">{Number(form.width) * Number(form.height)} total squares</p>
          )}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : isEdit ? 'Update Yard' : 'Create Yard'}
          </button>
          <Link to={isEdit ? `/yards/${id}` : '/yards'} className="btn btn-outline-dark">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
