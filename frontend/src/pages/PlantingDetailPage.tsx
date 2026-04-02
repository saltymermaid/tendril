import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface LifecyclePhase {
  phase: string
  phase_display: string
  day_number: number
  total_days: number
  phase_day: number
  phase_total_days: number
  progress_percent: number
}

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
  lifecycle: LifecyclePhase | null
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

const REMOVAL_REASONS = [
  { value: 'harvest_complete', label: '🌾 Harvest Complete' },
  { value: 'died', label: '💀 Died' },
  { value: 'pulled_early', label: '🔄 Pulled Early' },
  { value: 'pest_disease', label: '🐛 Pest / Disease' },
  { value: 'other', label: '📝 Other' },
]

export function PlantingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [planting, setPlanting] = useState<PlantingDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showRemoveModal, setShowRemoveModal] = useState(false)
  const [removalReason, setRemovalReason] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

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

  async function handleActivate() {
    setActionLoading(true)
    setError('')
    try {
      const res = await fetch(`/api/plantings/${id}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to activate')
      }
      setPlanting(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to activate planting')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleComplete() {
    if (!removalReason) {
      setError('Please select a removal reason')
      return
    }
    setActionLoading(true)
    setError('')
    try {
      const res = await fetch(`/api/plantings/${id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ removal_reason: removalReason }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to complete')
      }
      setPlanting(await res.json())
      setShowRemoveModal(false)
      setRemovalReason('')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to complete planting')
    } finally {
      setActionLoading(false)
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

  if (error && !planting) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Planting not found'}</div>
        <Link to="/containers" className="btn btn-outline-dark">← Back to Containers</Link>
      </div>
    )
  }

  if (!planting) return null

  const positionLabel = planting.tower_level !== null
    ? `Level ${planting.tower_level + 1}, Pocket ${planting.square_x + 1}`
    : `${ROW_LABELS[planting.square_y]}${planting.square_x + 1}${
        planting.square_width > 1 || planting.square_height > 1
          ? ` (${planting.square_width}×${planting.square_height})`
          : ''
      }`

  const lifecycle = planting.lifecycle

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
              <>
                <button
                  onClick={handleActivate}
                  className="btn btn-primary btn-sm"
                  disabled={actionLoading}
                >
                  🌱 Plant Now
                </button>
                <button onClick={handleDelete} className="btn btn-danger btn-sm">
                  Delete
                </button>
              </>
            )}
            {planting.status === 'in_progress' && (
              <button
                onClick={() => setShowRemoveModal(true)}
                className="btn btn-primary btn-sm"
              >
                ✓ Remove / Complete
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Lifecycle Phase Display */}
      {lifecycle && planting.status === 'in_progress' && (
        <div className="lifecycle-card">
          <div className="lifecycle-header">
            <span className={`lifecycle-phase-icon ${lifecycle.phase}`}>
              {lifecycle.phase === 'germination' && '🌱'}
              {lifecycle.phase === 'growing' && '🌿'}
              {lifecycle.phase === 'harvesting' && '🌾'}
            </span>
            <div className="lifecycle-info">
              <div className="lifecycle-phase-name">{lifecycle.phase_display}</div>
              <div className="lifecycle-day-count">
                Day {lifecycle.day_number + 1} of {lifecycle.total_days}
              </div>
            </div>
          </div>
          <div className="lifecycle-progress-bar">
            <div className="lifecycle-progress-track">
              <div
                className={`lifecycle-progress-fill ${lifecycle.phase}`}
                style={{ width: `${lifecycle.progress_percent}%` }}
              />
            </div>
            <div className="lifecycle-progress-label">
              {Math.round(lifecycle.progress_percent)}% complete
            </div>
          </div>
          {lifecycle.phase_total_days > 0 && (
            <div className="lifecycle-phase-progress">
              Phase progress: Day {lifecycle.phase_day + 1} of {lifecycle.phase_total_days}
            </div>
          )}
        </div>
      )}

      {lifecycle && planting.status === 'not_started' && (
        <div className="lifecycle-card planned">
          <div className="lifecycle-header">
            <span className="lifecycle-phase-icon not_started">📋</span>
            <div className="lifecycle-info">
              <div className="lifecycle-phase-name">Planned</div>
              <div className="lifecycle-day-count">
                Starts {planting.start_date} · {lifecycle.total_days} days planned
              </div>
            </div>
          </div>
        </div>
      )}

      {lifecycle && planting.status === 'complete' && (
        <div className="lifecycle-card complete">
          <div className="lifecycle-header">
            <span className="lifecycle-phase-icon complete">✅</span>
            <div className="lifecycle-info">
              <div className="lifecycle-phase-name">Complete</div>
              <div className="lifecycle-day-count">
                {planting.start_date} → {planting.end_date} · {lifecycle.total_days} days
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Info Grid */}
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
        <div className="container-info-item">
          <div className="info-label">Position</div>
          <div className="info-value">{positionLabel}</div>
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
            <div className="info-value">
              {REMOVAL_REASONS.find(r => r.value === planting.removal_reason)?.label
                || planting.removal_reason.replace('_', ' ')}
            </div>
          </div>
        )}
      </div>

      {error && <div className="form-message error">{error}</div>}

      {/* Remove / Complete Modal */}
      {showRemoveModal && (
        <div className="modal-overlay" onClick={() => setShowRemoveModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Remove Planting</h3>
              <button className="modal-close" onClick={() => setShowRemoveModal(false)}>×</button>
            </div>
            <div className="planting-detail-body">
              <p className="text-muted" style={{ marginBottom: '1rem' }}>
                Why is this planting being removed?
              </p>
              <div className="removal-reason-list">
                {REMOVAL_REASONS.map(reason => (
                  <button
                    key={reason.value}
                    className={`removal-reason-btn ${removalReason === reason.value ? 'selected' : ''}`}
                    onClick={() => setRemovalReason(reason.value)}
                  >
                    {reason.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="modal-actions">
              <button
                onClick={handleComplete}
                className="btn btn-primary"
                disabled={!removalReason || actionLoading}
              >
                {actionLoading ? 'Completing...' : 'Complete Planting'}
              </button>
              <button
                onClick={() => setShowRemoveModal(false)}
                className="btn btn-outline-dark"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
