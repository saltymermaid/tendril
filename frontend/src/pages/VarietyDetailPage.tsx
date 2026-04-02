import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface VarietyDetail {
  id: number
  user_id: number
  name: string
  category_id: number
  category_name: string | null
  category_color: string | null
  season_override_start_month: number | null
  season_override_start_day: number | null
  season_override_end_month: number | null
  season_override_end_day: number | null
  days_to_germination_min: number | null
  days_to_germination_max: number | null
  days_to_harvest_min: number | null
  days_to_harvest_max: number | null
  planting_depth: string | null
  spacing: string
  sunlight: string | null
  is_climbing: boolean
  planting_method: string
  seed_packet_photo_url: string | null
  source_url: string | null
  notes: string | null
}

const MONTH_NAMES = [
  '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

function formatRange(min: number | null, max: number | null, suffix: string): string {
  if (!min && !max) return '—'
  if (min && max && min !== max) return `${min}–${max} ${suffix}`
  return `${min || max} ${suffix}`
}

export function VarietyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [variety, setVariety] = useState<VarietyDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (id) fetchVariety()
  }, [id])

  async function fetchVariety() {
    try {
      const res = await fetch(`/api/varieties/${id}`)
      if (!res.ok) throw new Error('Variety not found')
      setVariety(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load variety')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this variety? This cannot be undone.')) return
    setDeleting(true)
    try {
      const res = await fetch(`/api/varieties/${id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to delete')
      }
      navigate(`/catalog/categories/${variety?.category_id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete variety')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading variety...</p>
      </div>
    )
  }

  if (error || !variety) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Variety not found'}</div>
        <Link to="/catalog" className="btn btn-outline-dark">← Back to Catalog</Link>
      </div>
    )
  }

  const hasSeasonOverride = variety.season_override_start_month != null

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to={`/catalog/categories/${variety.category_id}`} className="back-link">
          ← Back to {variety.category_name}
        </Link>
        <div className="page-header-row">
          <div className="category-title-row">
            <div
              className="category-color-dot-lg"
              style={{ backgroundColor: variety.category_color || '#ccc' }}
            />
            <div>
              <h2>{variety.name}</h2>
              <span className="text-muted">{variety.category_name}</span>
            </div>
          </div>
          <div className="page-header-actions">
            <Link to={`/catalog/varieties/${id}/edit`} className="btn btn-outline-dark btn-sm">
              Edit
            </Link>
            <button
              onClick={handleDelete}
              className="btn btn-danger btn-sm"
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </div>

      <div className="detail-grid">
        {/* Growth Info */}
        <div className="detail-card">
          <h3>Growth Information</h3>
          <dl className="detail-list">
            <div className="detail-item">
              <dt>Days to Germination</dt>
              <dd>{formatRange(variety.days_to_germination_min, variety.days_to_germination_max, 'days')}</dd>
            </div>
            <div className="detail-item">
              <dt>Days to Harvest</dt>
              <dd>{formatRange(variety.days_to_harvest_min, variety.days_to_harvest_max, 'days')}</dd>
            </div>
            <div className="detail-item">
              <dt>Planting Depth</dt>
              <dd>{variety.planting_depth || '—'}</dd>
            </div>
            <div className="detail-item">
              <dt>Spacing</dt>
              <dd>{variety.spacing}</dd>
            </div>
            <div className="detail-item">
              <dt>Sunlight</dt>
              <dd>{variety.sunlight ? variety.sunlight.replace('_', ' ') : '—'}</dd>
            </div>
            <div className="detail-item">
              <dt>Climbing</dt>
              <dd>{variety.is_climbing ? 'Yes' : 'No'}</dd>
            </div>
            <div className="detail-item">
              <dt>Planting Method</dt>
              <dd>{variety.planting_method.replace('_', ' ')}</dd>
            </div>
          </dl>
        </div>

        {/* Season Override */}
        {hasSeasonOverride && (
          <div className="detail-card">
            <h3>Season Override</h3>
            <p className="text-muted" style={{ marginBottom: 'var(--space-2)' }}>
              This variety overrides the category planting season.
            </p>
            <p>
              {MONTH_NAMES[variety.season_override_start_month!]} {variety.season_override_start_day}
              {' — '}
              {MONTH_NAMES[variety.season_override_end_month!]} {variety.season_override_end_day}
            </p>
          </div>
        )}

        {/* Notes */}
        {variety.notes && (
          <div className="detail-card">
            <h3>Notes</h3>
            <p className="variety-notes">{variety.notes}</p>
          </div>
        )}

        {/* Links */}
        {(variety.source_url || variety.seed_packet_photo_url) && (
          <div className="detail-card">
            <h3>Links & Media</h3>
            {variety.source_url && (
              <p>
                <a href={variety.source_url} target="_blank" rel="noopener noreferrer" className="external-link">
                  🔗 Source / Purchase Link
                </a>
              </p>
            )}
            {variety.seed_packet_photo_url && (
              <div className="seed-packet-preview">
                <img src={variety.seed_packet_photo_url} alt="Seed packet" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
