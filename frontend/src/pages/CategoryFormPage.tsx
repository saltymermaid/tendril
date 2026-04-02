import { apiFetch } from "../lib/api"
import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'

interface PlantingSeasonInput {
  usda_zone: string
  start_month: number
  start_day: number
  end_month: number
  end_day: number
}

interface CategoryFormData {
  name: string
  color: string
  harvest_type: string
  icon_svg: string
  planting_seasons: PlantingSeasonInput[]
}

const EMPTY_SEASON: PlantingSeasonInput = {
  usda_zone: '10a',
  start_month: 1,
  start_day: 1,
  end_month: 12,
  end_day: 31,
}

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]

export function CategoryFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [form, setForm] = useState<CategoryFormData>({
    name: '',
    color: '#22c55e',
    harvest_type: 'continuous',
    icon_svg: '',
    planting_seasons: [{ ...EMPTY_SEASON }],
  })
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isEdit && id) {
      fetchCategory()
    }
  }, [id])

  async function fetchCategory() {
    try {
      const res = await apiFetch(`/api/categories/${id}`)
      if (!res.ok) throw new Error('Category not found')
      const data = await res.json()
      setForm({
        name: data.name,
        color: data.color,
        harvest_type: data.harvest_type,
        icon_svg: data.icon_svg || '',
        planting_seasons: data.planting_seasons.length > 0
          ? data.planting_seasons.map((ps: PlantingSeasonInput) => ({
              usda_zone: ps.usda_zone,
              start_month: ps.start_month,
              start_day: ps.start_day,
              end_month: ps.end_month,
              end_day: ps.end_day,
            }))
          : [{ ...EMPTY_SEASON }],
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load category')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const body = {
        name: form.name,
        color: form.color,
        harvest_type: form.harvest_type,
        icon_svg: form.icon_svg || null,
        planting_seasons: form.planting_seasons,
      }

      const url = isEdit ? `/api/categories/${id}` : '/api/categories'
      const method = isEdit ? 'PUT' : 'POST'

      const res = await apiFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save category')
      }

      const saved = await res.json()
      navigate(`/catalog/categories/${saved.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save category')
    } finally {
      setSaving(false)
    }
  }

  function updateSeason(index: number, field: keyof PlantingSeasonInput, value: string | number) {
    setForm((prev) => {
      const seasons = [...prev.planting_seasons]
      seasons[index] = { ...seasons[index], [field]: value }
      return { ...prev, planting_seasons: seasons }
    })
  }

  function addSeason() {
    setForm((prev) => ({
      ...prev,
      planting_seasons: [...prev.planting_seasons, { ...EMPTY_SEASON }],
    }))
  }

  function removeSeason(index: number) {
    setForm((prev) => ({
      ...prev,
      planting_seasons: prev.planting_seasons.filter((_, i) => i !== index),
    }))
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
        <Link to={isEdit ? `/catalog/categories/${id}` : '/catalog'} className="back-link">
          ← {isEdit ? 'Back to Category' : 'Back to Catalog'}
        </Link>
        <h2>{isEdit ? 'Edit Category' : 'New Category'}</h2>
      </div>

      {error && <div className="form-message error">{error}</div>}

      <form onSubmit={handleSubmit} className="detail-form">
        <div className="form-card">
          <div className="form-group">
            <label className="form-label">Name</label>
            <input
              type="text"
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              placeholder="e.g., Tomatoes"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Color</label>
              <div className="color-input-row">
                <input
                  type="color"
                  value={form.color}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                  className="color-picker"
                />
                <input
                  type="text"
                  className="input"
                  value={form.color}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                  pattern="^#[0-9a-fA-F]{6}$"
                  placeholder="#22c55e"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Harvest Type</label>
              <select
                className="input"
                value={form.harvest_type}
                onChange={(e) => setForm({ ...form, harvest_type: e.target.value })}
              >
                <option value="continuous">Continuous</option>
                <option value="single">Single</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Icon SVG (optional)</label>
            <div className="icon-upload-row">
              <input
                type="file"
                accept=".svg,image/svg+xml"
                className="input"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (!file) return
                  const reader = new FileReader()
                  reader.onload = (evt) => {
                    const text = evt.target?.result as string
                    setForm((prev) => ({ ...prev, icon_svg: text || '' }))
                  }
                  reader.readAsText(file)
                  // reset input so same file can be re-selected
                  e.target.value = ''
                }}
              />
              {form.icon_svg && (
                <button
                  type="button"
                  className="btn btn-outline-dark btn-sm"
                  onClick={() => setForm((prev) => ({ ...prev, icon_svg: '' }))}
                >
                  Clear
                </button>
              )}
            </div>
            {form.icon_svg && (
              <div className="icon-preview">
                <span className="form-label">Preview:</span>
                <span
                  className="icon-preview-svg"
                  dangerouslySetInnerHTML={{ __html: form.icon_svg }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Planting Seasons */}
        <div className="form-card">
          <div className="section-header-row">
            <h3>Planting Seasons</h3>
            <button type="button" onClick={addSeason} className="btn btn-outline-dark btn-sm">
              + Add Season
            </button>
          </div>

          {form.planting_seasons.map((season, idx) => (
            <div key={idx} className="season-form-row">
              <div className="form-group">
                <label className="form-label">USDA Zone</label>
                <input
                  type="text"
                  className="input"
                  value={season.usda_zone}
                  onChange={(e) => updateSeason(idx, 'usda_zone', e.target.value)}
                  placeholder="10a"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Start</label>
                <div className="date-row">
                  <select
                    className="input"
                    value={season.start_month}
                    onChange={(e) => updateSeason(idx, 'start_month', parseInt(e.target.value))}
                  >
                    {MONTHS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    className="input day-input"
                    value={season.start_day}
                    onChange={(e) => updateSeason(idx, 'start_day', parseInt(e.target.value) || 1)}
                    min={1}
                    max={31}
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">End</label>
                <div className="date-row">
                  <select
                    className="input"
                    value={season.end_month}
                    onChange={(e) => updateSeason(idx, 'end_month', parseInt(e.target.value))}
                  >
                    {MONTHS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    className="input day-input"
                    value={season.end_day}
                    onChange={(e) => updateSeason(idx, 'end_day', parseInt(e.target.value) || 1)}
                    min={1}
                    max={31}
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
              </div>
              {form.planting_seasons.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeSeason(idx)}
                  className="btn btn-danger btn-sm season-remove"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : isEdit ? 'Update Category' : 'Create Category'}
          </button>
          <Link
            to={isEdit ? `/catalog/categories/${id}` : '/catalog'}
            className="btn btn-outline-dark"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
