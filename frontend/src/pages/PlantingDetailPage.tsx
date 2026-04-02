import { useEffect, useState, useCallback } from 'react'
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

interface EventData {
  id: number
  event_type: string
  date: string
  quantity: number | null
  unit: string | null
  notes: string | null
  created_at: string
  container_name: string | null
  variety_name: string | null
  category_color: string | null
}

interface NoteData {
  id: number
  content: string
  date: string
  photo_url: string | null
  created_at: string
  updated_at: string
  container_name: string | null
  variety_name: string | null
  category_color: string | null
}

type TimelineItem = {
  type: 'event'
  date: string
  data: EventData
} | {
  type: 'note'
  date: string
  data: NoteData
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

const REMOVAL_REASONS = [
  { value: 'harvest_complete', label: '🌾 Harvest Complete' },
  { value: 'died', label: '💀 Died' },
  { value: 'pulled_early', label: '🔄 Pulled Early' },
  { value: 'pest_disease', label: '🐛 Pest / Disease' },
  { value: 'other', label: '📝 Other' },
]

const HARVEST_UNITS = [
  { value: 'count', label: 'Count' },
  { value: 'lbs', label: 'Pounds' },
  { value: 'oz', label: 'Ounces' },
  { value: 'bunches', label: 'Bunches' },
  { value: 'each', label: 'Each' },
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

  // Events & Notes
  const [events, setEvents] = useState<EventData[]>([])
  const [notes, setNotes] = useState<NoteData[]>([])

  // Harvest modal
  const [showHarvestModal, setShowHarvestModal] = useState(false)
  const [harvestQuantity, setHarvestQuantity] = useState('')
  const [harvestUnit, setHarvestUnit] = useState('count')
  const [harvestDate, setHarvestDate] = useState(new Date().toISOString().split('T')[0])
  const [harvestNotes, setHarvestNotes] = useState('')

  // Note modal
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [noteContent, setNoteContent] = useState('')
  const [noteDate, setNoteDate] = useState(new Date().toISOString().split('T')[0])

  useEffect(() => {
    if (id) fetchPlanting()
  }, [id])

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch(`/api/events?planting_id=${id}`)
      if (res.ok) setEvents(await res.json())
    } catch { /* ignore */ }
  }, [id])

  const fetchNotes = useCallback(async () => {
    try {
      const res = await fetch(`/api/notes?planting_id=${id}`)
      if (res.ok) setNotes(await res.json())
    } catch { /* ignore */ }
  }, [id])

  useEffect(() => {
    if (id) {
      fetchEvents()
      fetchNotes()
    }
  }, [id, fetchEvents, fetchNotes])

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
      fetchEvents() // Refresh events to show auto-created planting event
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

  async function handleLogHarvest(e: React.FormEvent) {
    e.preventDefault()
    if (!planting) return
    setActionLoading(true)
    setError('')
    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: 'harvest',
          date: harvestDate,
          container_id: planting.container_id,
          planting_id: planting.id,
          variety_id: planting.variety_id,
          square_x: planting.square_x,
          square_y: planting.square_y,
          tower_level: planting.tower_level,
          quantity: parseInt(harvestQuantity) || 0,
          unit: harvestUnit,
          notes: harvestNotes || null,
        }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to log harvest')
      }
      setShowHarvestModal(false)
      setHarvestQuantity('')
      setHarvestUnit('count')
      setHarvestNotes('')
      setHarvestDate(new Date().toISOString().split('T')[0])
      fetchEvents()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to log harvest')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault()
    if (!planting) return
    setActionLoading(true)
    setError('')
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: noteContent,
          date: noteDate,
          container_id: planting.container_id,
          planting_id: planting.id,
          variety_id: planting.variety_id,
          square_x: planting.square_x,
          square_y: planting.square_y,
          tower_level: planting.tower_level,
        }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to add note')
      }
      setShowNoteModal(false)
      setNoteContent('')
      setNoteDate(new Date().toISOString().split('T')[0])
      fetchNotes()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to add note')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleDeleteNote(noteId: number) {
    if (!confirm('Delete this note?')) return
    try {
      const res = await fetch(`/api/notes/${noteId}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete note')
      fetchNotes()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete note')
    }
  }

  async function handleDeleteEvent(eventId: number) {
    if (!confirm('Delete this event?')) return
    try {
      const res = await fetch(`/api/events/${eventId}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete event')
      fetchEvents()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete event')
    }
  }

  // Build combined timeline
  const timeline: TimelineItem[] = [
    ...events.map(e => ({ type: 'event' as const, date: e.date, data: e })),
    ...notes.map(n => ({ type: 'note' as const, date: n.date, data: n })),
  ].sort((a, b) => b.date.localeCompare(a.date))

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
              <>
                <button
                  onClick={() => setShowHarvestModal(true)}
                  className="btn btn-primary btn-sm"
                >
                  🌾 Log Harvest
                </button>
                <button
                  onClick={() => setShowRemoveModal(true)}
                  className="btn btn-outline-dark btn-sm"
                >
                  ✓ Remove / Complete
                </button>
              </>
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

      {/* Harvest Summary */}
      {events.filter(e => e.event_type === 'harvest').length > 0 && (
        <div className="harvest-summary">
          <h3>🌾 Harvest Totals</h3>
          <div className="harvest-totals">
            {Object.entries(
              events
                .filter(e => e.event_type === 'harvest')
                .reduce((acc, e) => {
                  const unit = e.unit || 'count'
                  acc[unit] = (acc[unit] || 0) + (e.quantity || 0)
                  return acc
                }, {} as Record<string, number>)
            ).map(([unit, total]) => (
              <span key={unit} className="harvest-total-badge">
                {total} {unit}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Activity Timeline */}
      <div className="activity-timeline">
        <div className="timeline-header">
          <h3>Activity</h3>
          <button
            onClick={() => {
              setNoteDate(new Date().toISOString().split('T')[0])
              setShowNoteModal(true)
            }}
            className="btn btn-outline-dark btn-sm"
          >
            📝 Add Note
          </button>
        </div>

        {timeline.length === 0 ? (
          <p className="text-muted" style={{ padding: '1rem 0' }}>
            No activity yet. Events and notes will appear here.
          </p>
        ) : (
          <div className="timeline-list">
            {timeline.map(item => (
              <div key={`${item.type}-${item.data.id}`} className="timeline-item">
                <div className="timeline-item-icon">
                  {item.type === 'event' ? (
                    (item.data as EventData).event_type === 'harvest' ? '🌾' : '🌱'
                  ) : '📝'}
                </div>
                <div className="timeline-item-content">
                  <div className="timeline-item-header">
                    <span className="timeline-item-title">
                      {item.type === 'event' ? (
                        (item.data as EventData).event_type === 'harvest'
                          ? `Harvested ${(item.data as EventData).quantity || ''} ${(item.data as EventData).unit || ''}`
                          : 'Planted'
                      ) : 'Note'}
                    </span>
                    <span className="timeline-item-date">{item.date}</span>
                  </div>
                  {item.type === 'event' && (item.data as EventData).notes && (
                    <p className="timeline-item-text">{(item.data as EventData).notes}</p>
                  )}
                  {item.type === 'note' && (
                    <p className="timeline-item-text">{(item.data as NoteData).content}</p>
                  )}
                  <button
                    className="timeline-item-delete"
                    onClick={() => {
                      if (item.type === 'event') handleDeleteEvent(item.data.id)
                      else handleDeleteNote(item.data.id)
                    }}
                    title="Delete"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
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

      {/* Harvest Modal */}
      {showHarvestModal && (
        <div className="modal-overlay" onClick={() => setShowHarvestModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🌾 Log Harvest</h3>
              <button className="modal-close" onClick={() => setShowHarvestModal(false)}>×</button>
            </div>
            <form onSubmit={handleLogHarvest} style={{ marginTop: 'var(--space-2)' }}>
              <div className="planting-detail-body">
                <div className="form-group">
                  <label className="form-label">Quantity *</label>
                  <input
                    type="number"
                    className="form-input"
                    min="1"
                    value={harvestQuantity}
                    onChange={e => setHarvestQuantity(e.target.value)}
                    required
                    placeholder="How many?"
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Unit</label>
                  <select className="form-input" value={harvestUnit} onChange={e => setHarvestUnit(e.target.value)}>
                    {HARVEST_UNITS.map(u => (
                      <option key={u.value} value={u.value}>{u.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={harvestDate}
                    onChange={e => setHarvestDate(e.target.value)}
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Notes (optional)</label>
                  <textarea
                    className="form-input"
                    value={harvestNotes}
                    onChange={e => setHarvestNotes(e.target.value)}
                    rows={2}
                    placeholder="Any notes about this harvest..."
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!harvestQuantity || actionLoading}
                >
                  {actionLoading ? 'Saving...' : 'Log Harvest'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowHarvestModal(false)}
                  className="btn btn-outline-dark"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Note Modal */}
      {showNoteModal && (
        <div className="modal-overlay" onClick={() => setShowNoteModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📝 Add Note</h3>
              <button className="modal-close" onClick={() => setShowNoteModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddNote} style={{ marginTop: 'var(--space-2)' }}>
              <div className="planting-detail-body">
                <div className="form-group">
                  <label className="form-label">Note *</label>
                  <textarea
                    className="form-input"
                    value={noteContent}
                    onChange={e => setNoteContent(e.target.value)}
                    rows={4}
                    required
                    placeholder="What's happening with this plant?"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={noteDate}
                    onChange={e => setNoteDate(e.target.value)}
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!noteContent.trim() || actionLoading}
                >
                  {actionLoading ? 'Saving...' : 'Save Note'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowNoteModal(false)}
                  className="btn btn-outline-dark"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
