import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface PlantingDetail {
  id: number
  user_id: number
  container_id: number
  variety_id: number
  square_x: number
  square_y: number
  square_width: number
  square_height: number
  tower_level: number | null
  start_date: string
  end_date: string
  status: string
  planting_method: string | null
  quantity: number | null
  removal_reason: string | null
  variety_name: string | null
  category_name: string | null
  category_color: string | null
  container_name: string | null
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

export function PlantingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [planting, setPlanting] = useState<PlantingDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (id) fetchPlanting()
  }, [id])

  async function fetchPlanting() {
    try {
      const res = await fetch(`/api/plantings/${id}`)
      if (!res.ok) throw new Error('Planting not found')
      setPlanting(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load planting')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this planting?')) return
    try {
      const res = await fetch(`/api/plantings/${id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to delete')
      }
      navigate(planting ? `/containers/${planting.container_id}` : '/containers')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
    }
  }

  async function updateStatus(newStatus: string) {
    try {
      const res = await fetch(`/api/plantings/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to update')
      }
      setPlanting(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading planting...</p>
      </div>
    )
  }

  if (error || !planting) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Planting not found'}</div>
        <Link to="/containers" className="btn btn-outline-dark">← Back to Containers</Link>
      </div>
    )
  }

  const positionLabel = planting.tower_level !== null
    ? `Level ${planting.tower_level + 1}, Pocket ${planting.square_x + 1}`
    : `${ROW_LABELS[planting.square_y]}${planting.square_x + 1}${
        planting.square_width > 1 || planting.square_height > 1
          ? ` (${planting.square_width}×${planting.square_height})`
          : ''
      }`

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to={`/containers/${planting.container_id}`} className="back-link">
          ← Back to {planting.container_name || 'Container'}
        </Link>
        <div className="page-header-row">
          <div>
            <h2>
              <span
                className="planting-color-dot inline"
                style={{ backgroundColor: planting.category_color || '#ccc' }}
              />
              {planting.variety_name}
            </h2>
            <span className="text-muted">
              {planting.category_name} · {positionLabel}
            </span>
          </div>
          <div className="page-header-actions">
            {planting.status === 'not_started' && (
              <button
                onClick={() => updateStatus('in_progress')}
                className="btn btn-primary btn-sm"
              >
                ▶ Start Growing
              </button>
            )}
            {planting.status === 'in_progress' && (
              <button
                onClick={() => updateStatus('complete')}
                className="btn btn-primary btn-sm"
              >
                ✓ Mark Complete
              </button>
            )}
            {planting.status === 'not_started' && (
              <button onClick={handleDelete} className="btn btn-danger btn-sm">
                Delete
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="container-info-grid">
        <div className="container-info-item">
          <div className="info-label">Status</div>
          <div className="info-value">
            <span className={`status-badge ${planting.status}`}>
              {planting.status.replace('_', ' ')}
            </span>
          </div>
        </div>
        <div className="container-info-item">
          <div className="info-label">Start Date</div>
          <div className="info-value">{planting.start_date}</div>
        </div>
        <div className="container-info-item">
          <div className="info-label">End Date</div>
          <div className="info-value">{planting.end_date}</div>
        </div>
        <div className="container-info-item">
          <div className="info-label">Container</div>
          <div className="info-value">
            <Link to={`/containers/${planting.container_id}`}>
              {planting.container_name}
            </Link>
          </div>
        </div>
        {planting.planting_method && (
          <div className="container-info-item">
            <div className="info-label">Method</div>
            <div className="info-value">{planting.planting_method.replace('_', ' ')}</div>
          </div>
        )}
        {planting.quantity && (
          <div className="container-info-item">
            <div className="info-label">Quantity</div>
            <div className="info-value">{planting.quantity}</div>
          </div>
        )}
        {planting.removal_reason && (
          <div className="container-info-item">
            <div className="info-label">Removal Reason</div>
            <div className="info-value">{planting.removal_reason.replace('_', ' ')}</div>
          </div>
        )}
      </div>

      {error && <div className="form-message error">{error}</div>}
    </div>
  )
}
