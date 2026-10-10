import { apiFetch } from "../lib/api"
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface PlantStartAllocation {
  planting_id: number
  container_id: number
  container_name: string | null
  start_date: string
  status: 'not_started' | 'in_progress' | 'complete'
  quantity: number
}

interface PlantStart {
  id: number
  variety_id: number
  variety_name: string | null
  category_name: string | null
  category_color: string | null
  start_date: string
  quantity: number // available — not yet assigned to a bed
  planned_quantity: number // reserved by a planned planting, still in the tray
  transplanted_quantity: number // already in the ground
  total_quantity: number
  allocations: PlantStartAllocation[]
}

interface Variety {
  id: number
  name: string
  category_name: string | null
  category_color: string | null
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const UNCATEGORIZED = 'Uncategorized'

function categoryOf(s: PlantStart): string {
  return s.category_name || UNCATEGORIZED
}

export function StartsPage() {
  const [starts, setStarts] = useState<PlantStart[]>([])
  const [varieties, setVarieties] = useState<Variety[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showUsed, setShowUsed] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null)

  const [showAddModal, setShowAddModal] = useState(false)
  const [form, setForm] = useState({
    variety_id: '',
    start_date: new Date().toISOString().split('T')[0],
    quantity: '1',
  })
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchStarts = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/plant-starts?include_used=${showUsed}`)
      if (!res.ok) throw new Error('Failed to load starts')
      setStarts(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load starts')
    } finally {
      setLoading(false)
    }
  }, [showUsed])

  const fetchVarieties = useCallback(async () => {
    try {
      const res = await apiFetch('/api/varieties')
      if (res.ok) setVarieties(await res.json())
    } catch (err) {
      console.error('Failed to fetch varieties:', err)
    }
  }, [])

  useEffect(() => {
    fetchStarts()
  }, [fetchStarts])

  useEffect(() => {
    fetchVarieties()
  }, [fetchVarieties])

  function openAddModal() {
    setFormError('')
    setShowAddModal(true)
    fetchVarieties()
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!form.variety_id) {
      setFormError('Pick a variety')
      return
    }
    const quantity = parseInt(form.quantity, 10)
    if (!quantity || quantity < 1) {
      setFormError('Quantity must be at least 1')
      return
    }

    setSubmitting(true)
    setFormError('')
    try {
      const res = await apiFetch('/api/plant-starts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          variety_id: parseInt(form.variety_id, 10),
          start_date: form.start_date,
          quantity,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail || 'Failed to create start')
      }
      setShowAddModal(false)
      setForm({ variety_id: '', start_date: new Date().toISOString().split('T')[0], quantity: '1' })
      fetchStarts()
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create start')
    } finally {
      setSubmitting(false)
    }
  }

  async function adjustQuantity(start: PlantStart, delta: number) {
    const newQuantity = Math.max(0, start.quantity + delta)
    const totalDelta = newQuantity - start.quantity
    setStarts((prev) =>
      prev.map((s) =>
        s.id === start.id ? { ...s, quantity: newQuantity, total_quantity: s.total_quantity + totalDelta } : s
      )
    )
    try {
      const res = await apiFetch(`/api/plant-starts/${start.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: newQuantity }),
      })
      if (!res.ok) throw new Error()
      if (newQuantity === 0 && start.planned_quantity === 0 && !showUsed) {
        setStarts((prev) => prev.filter((s) => s.id !== start.id))
      }
    } catch {
      fetchStarts()
    }
  }

  async function handleDelete(start: PlantStart) {
    if (!confirm(`Delete this start (${start.variety_name}, ${formatDate(start.start_date)})?`)) return
    try {
      const res = await apiFetch(`/api/plant-starts/${start.id}`, { method: 'DELETE' })
      if (res.ok) setStarts((prev) => prev.filter((s) => s.id !== start.id))
    } catch (err) {
      console.error('Failed to delete start:', err)
    }
  }

  // Pill counts: available / still in trays (available + planned). Transplanted
  // seedlings are in the ground, so they no longer count as starts on hand.
  const categoryPills = Array.from(
    starts.reduce((acc, s) => {
      const name = categoryOf(s)
      const entry = acc.get(name) || { color: s.category_color || '#ccc', available: 0, inTray: 0 }
      entry.available += s.quantity
      entry.inTray += s.quantity + s.planned_quantity
      acc.set(name, entry)
      return acc
    }, new Map<string, { color: string; available: number; inTray: number }>())
  ).sort((a, b) => a[0].localeCompare(b[0]))

  const activeFilter = categoryPills.some(([name]) => name === categoryFilter) ? categoryFilter : null
  const visibleStarts = activeFilter ? starts.filter((s) => categoryOf(s) === activeFilter) : starts

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading starts...</p>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Starts</h2>
          <p className="page-subtitle">
            Seedlings in your trays — planned ones are reserved for a bed until they go in the ground
          </p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={openAddModal}>
            + Add a Start
          </button>
        </div>
      </div>

      {categoryPills.length > 0 && (
        <div className="category-filter-chips starts-filter-chips">
          <button
            type="button"
            className={`chip ${!activeFilter ? 'active' : ''}`}
            onClick={() => setCategoryFilter(null)}
          >
            All
          </button>
          {categoryPills.map(([name, { color, available, inTray }]) => (
            <button
              key={name}
              type="button"
              className={`chip ${activeFilter === name ? 'active' : ''}`}
              style={activeFilter === name ? { backgroundColor: color, borderColor: color, color: '#fff' } : undefined}
              onClick={() => setCategoryFilter(activeFilter === name ? null : name)}
              title={`${available} available of ${inTray} in trays`}
            >
              {name} <span className="chip-count">{available}/{inTray}</span>
            </button>
          ))}
        </div>
      )}

      <label className="form-label" style={{ marginBottom: 'var(--space-3)', display: 'inline-flex', alignItems: 'center' }}>
        <input
          type="checkbox"
          checked={showUsed}
          onChange={(e) => setShowUsed(e.target.checked)}
          style={{ marginRight: 'var(--space-2)' }}
        />
        Show used up
      </label>

      {error && <div className="form-message error">{error}</div>}

      {starts.length === 0 && !error ? (
        <div className="empty-state">
          <span className="empty-icon">🌱</span>
          <h3>No starts yet</h3>
          <p>
            Record what you've started in trays so you can pick them when it's time to
            transplant into a bed.
          </p>
          <button className="btn btn-primary" onClick={openAddModal}>
            + Add a Start
          </button>
        </div>
      ) : (
        <div className="task-list">
          {visibleStarts.map((s) => (
            <div
              key={s.id}
              className={`task-card ${s.quantity === 0 && s.planned_quantity === 0 ? 'task-done' : ''}`}
            >
              <div className="task-card-main">
                <div className="task-card-header">
                  <span
                    className="variety-picker-dot"
                    style={{ backgroundColor: s.category_color || '#ccc' }}
                  />
                  <h4 className="task-title">{s.variety_name || 'Unknown variety'}</h4>
                </div>
                <div className="task-meta">
                  <span className="task-due">📅 Started {formatDate(s.start_date)}</span>
                  {s.category_name && <span className="task-variety">{s.category_name}</span>}
                </div>
                <StartBreakdown start={s} />
              </div>
              <div className="task-card-actions">
                <button
                  className="btn btn-sm btn-outline-dark"
                  onClick={() => adjustQuantity(s, -1)}
                  disabled={s.quantity === 0}
                  title="Decrease available (e.g. a seedling died)"
                >
                  −
                </button>
                <span className="start-available-count" title="Available to assign">
                  {s.quantity}
                  <small>avail</small>
                </span>
                <button
                  className="btn btn-sm btn-outline-dark"
                  onClick={() => adjustQuantity(s, 1)}
                  title="Increase available"
                >
                  +
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleDelete(s)}
                  title="Delete"
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add a Start</h3>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Variety *</label>
                <select
                  className="form-input"
                  value={form.variety_id}
                  onChange={(e) => setForm({ ...form, variety_id: e.target.value })}
                  required
                  autoFocus
                >
                  <option value="">— Select —</option>
                  {varieties.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </select>
                {varieties.length === 0 && (
                  <p className="text-muted">
                    No varieties yet. <Link to="/catalog/varieties/new">Add one</Link>
                  </p>
                )}
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Start Date *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    required
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Quantity *</label>
                  <input
                    type="number"
                    className="form-input"
                    min="1"
                    value={form.quantity}
                    onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                    required
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
              </div>

              {formError && <div className="form-message error">{formError}</div>}

              <div className="modal-actions">
                <button type="button" className="btn btn-outline-dark" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Adding...' : 'Add Start'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function StartBreakdown({ start }: { start: PlantStart }) {
  const { total_quantity: total, transplanted_quantity: transplanted, planned_quantity: planned, quantity: available } = start
  if (total === 0) return null

  const plannedAllocations = start.allocations.filter((a) => a.status === 'not_started')
  const segments = [
    { key: 'transplanted', count: transplanted },
    { key: 'planned', count: planned },
    { key: 'available', count: available },
  ].filter((seg) => seg.count > 0)

  return (
    <div className="start-breakdown">
      <div className="start-breakdown-bar" aria-hidden="true">
        {segments.map((seg) => (
          <span
            key={seg.key}
            className={`start-breakdown-seg seg-${seg.key}`}
            style={{ flexGrow: seg.count }}
          />
        ))}
      </div>
      <div className="start-breakdown-legend">
        <span>{total} started</span>
        {transplanted > 0 && <span className="legend-transplanted">{transplanted} in ground</span>}
        {planned > 0 && <span className="legend-planned">{planned} planned</span>}
        <span className="legend-available">{available} available</span>
      </div>
      {plannedAllocations.length > 0 && (
        <ul className="start-allocations">
          {plannedAllocations.map((a) => (
            <li key={a.planting_id}>
              <Link to={`/containers/${a.container_id}`}>
                {a.quantity} → {a.container_name || 'bed'} on {formatShortDate(a.start_date)}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
