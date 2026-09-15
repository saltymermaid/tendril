import { apiFetch } from "../lib/api"
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface PlantStart {
  id: number
  variety_id: number
  variety_name: string | null
  category_name: string | null
  category_color: string | null
  start_date: string
  quantity: number
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

export function StartsPage() {
  const [starts, setStarts] = useState<PlantStart[]>([])
  const [varieties, setVarieties] = useState<Variety[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showUsed, setShowUsed] = useState(false)

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
    setStarts((prev) => prev.map((s) => (s.id === start.id ? { ...s, quantity: newQuantity } : s)))
    try {
      const res = await apiFetch(`/api/plant-starts/${start.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: newQuantity }),
      })
      if (!res.ok) throw new Error()
      if (newQuantity === 0 && !showUsed) {
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
            Seedlings you've started but haven't planted into a bed yet
          </p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={openAddModal}>
            + Add a Start
          </button>
        </div>
      </div>

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
          {starts.map((s) => (
            <div key={s.id} className={`task-card ${s.quantity === 0 ? 'task-done' : ''}`}>
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
              </div>
              <div className="task-card-actions">
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => adjustQuantity(s, -1)}
                  disabled={s.quantity === 0}
                  title="Decrease quantity"
                >
                  −
                </button>
                <span style={{ minWidth: '2ch', textAlign: 'center', fontWeight: 600 }}>
                  {s.quantity}
                </span>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => adjustQuantity(s, 1)}
                  title="Increase quantity"
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
                <button type="button" className="btn btn-outline" onClick={() => setShowAddModal(false)}>
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
