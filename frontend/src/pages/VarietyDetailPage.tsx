import { apiFetch } from "../lib/api"
import { useEffect, useState, useCallback } from 'react'
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
  seed_start_days: number | null
  planting_depth: string | null
  spacing: string
  sunlight: string | null
  is_climbing: boolean
  planting_method: string
  seed_packet_photo_url: string | null
  source_url: string | null
  notes: string | null
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
}

interface NoteData {
  id: number
  content: string
  date: string
  photo_url: string | null
  created_at: string
  container_name: string | null
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

  // Events & Notes
  const [events, setEvents] = useState<EventData[]>([])
  const [notes, setNotes] = useState<NoteData[]>([])

  // Note modal
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [noteContent, setNoteContent] = useState('')
  const [noteDate, setNoteDate] = useState(new Date().toISOString().split('T')[0])
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (id) fetchVariety()
  }, [id])

  const fetchEvents = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/events?variety_id=${id}`)
      if (res.ok) setEvents(await res.json())
    } catch { /* ignore */ }
  }, [id])

  const fetchNotes = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/notes?variety_id=${id}`)
      if (res.ok) setNotes(await res.json())
    } catch { /* ignore */ }
  }, [id])

  useEffect(() => {
    if (id) {
      fetchEvents()
      fetchNotes()
    }
  }, [id, fetchEvents, fetchNotes])

  async function fetchVariety() {
    try {
      const res = await apiFetch(`/api/varieties/${id}`)
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
      const res = await apiFetch(`/api/varieties/${id}`, { method: 'DELETE' })
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

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault()
    if (!variety) return
    setActionLoading(true)
    setError('')
    try {
      const res = await apiFetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: noteContent,
          date: noteDate,
          variety_id: variety.id,
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
      const res = await apiFetch(`/api/notes/${noteId}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete note')
      fetchNotes()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete note')
    }
  }

  // Build combined timeline
  const timeline: TimelineItem[] = [
    ...events.map((e: EventData) => ({ type: 'event' as const, date: e.date, data: e })),
    ...notes.map((n: NoteData) => ({ type: 'note' as const, date: n.date, data: n })),
  ].sort((a, b) => b.date.localeCompare(a.date))

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading variety...</p>
      </div>
    )
  }

  if (error && !variety) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Variety not found'}</div>
        <Link to="/catalog" className="btn btn-outline-dark">← Back to Catalog</Link>
      </div>
    )
  }

  if (!variety) return null

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
            {variety.seed_start_days && (
              <div className="detail-item">
                <dt>Days in Tray</dt>
                <dd>{variety.seed_start_days} days before transplanting</dd>
              </div>
            )}
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

      {/* Harvest Summary for this variety */}
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
                      {item.data.container_name && (
                        <span className="text-muted" style={{ fontWeight: 400 }}>
                          {' '}in {item.data.container_name}
                        </span>
                      )}
                    </span>
                    <span className="timeline-item-date">{item.date}</span>
                  </div>
                  {item.type === 'event' && (item.data as EventData).notes && (
                    <p className="timeline-item-text">{(item.data as EventData).notes}</p>
                  )}
                  {item.type === 'note' && (
                    <p className="timeline-item-text">{(item.data as NoteData).content}</p>
                  )}
                  {item.type === 'note' && (
                    <button
                      className="timeline-item-delete"
                      onClick={() => handleDeleteNote(item.data.id)}
                      title="Delete"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && <div className="form-message error">{error}</div>}

      {/* Note Modal */}
      {showNoteModal && (
        <div className="modal-overlay" onClick={() => setShowNoteModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📝 Add Note for {variety.name}</h3>
              <button className="modal-close" onClick={() => setShowNoteModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddNote}>
              <div className="planting-detail-body">
                <div className="form-group">
                  <label>Note *</label>
                  <textarea
                    value={noteContent}
                    onChange={e => setNoteContent(e.target.value)}
                    rows={4}
                    required
                    placeholder="Observations about this variety..."
                  />
                </div>
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    value={noteDate}
                    onChange={e => setNoteDate(e.target.value)}
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
