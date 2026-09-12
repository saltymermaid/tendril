import { apiFetch } from "../lib/api"
import { useEffect, useState, useCallback } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface YardObj {
  id: number
  yard_id: number
  object_type: string
  container_id: number | null
  container_name: string | null
  label: string | null
  square_x: number
  square_y: number
  square_width: number
  square_height: number
}

interface YardDetail {
  id: number
  user_id: number
  name: string
  width: number
  height: number
  objects: YardObj[]
}

interface ContainerOption {
  id: number
  name: string
  type: string
  width: number | null
  height: number | null
  is_placed: boolean
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
function rowLabel(y: number): string {
  return y < ROW_LABELS.length ? ROW_LABELS[y] : String(y + 1)
}

const FEATURE_TYPES: { value: string; label: string; icon: string }[] = [
  { value: 'path', label: 'Path', icon: '🚶' },
  { value: 'mulch', label: 'Mulch', icon: '🟫' },
  { value: 'building', label: 'Building', icon: '🏠' },
  { value: 'tree', label: 'Tree', icon: '🌳' },
  { value: 'water', label: 'Water Feature', icon: '💧' },
  { value: 'other', label: 'Other', icon: '📍' },
]

const OBJECT_ICONS: Record<string, string> = {
  bed: '🌿', path: '🚶', mulch: '🟫', building: '🏠', tree: '🌳', water: '💧', other: '📍',
}

function objectDisplayName(obj: YardObj): string {
  return obj.object_type === 'bed' ? (obj.container_name || 'Bed') : (obj.label || FEATURE_TYPES.find(f => f.value === obj.object_type)?.label || obj.object_type)
}

export function YardDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [yard, setYard] = useState<YardDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const [mode, setMode] = useState<'display' | 'planning'>('display')
  const [moving, setMoving] = useState<YardObj | null>(null)
  const [moveError, setMoveError] = useState('')
  const [moveSubmitting, setMoveSubmitting] = useState(false)

  const [availableBeds, setAvailableBeds] = useState<ContainerOption[]>([])

  // Empty-square chooser (place bed vs add feature)
  const [chooser, setChooser] = useState<{ x: number; y: number } | null>(null)
  const [chooserMode, setChooserMode] = useState<'choose' | 'bed' | 'feature'>('choose')
  const [chooserError, setChooserError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [bedForm, setBedForm] = useState<{ containerId: number | '' }>({ containerId: '' })
  const [featureForm, setFeatureForm] = useState({
    object_type: 'path',
    label: '',
    square_width: 1,
    square_height: 1,
  })

  // Occupied-square detail/edit
  const [selectedObject, setSelectedObject] = useState<YardObj | null>(null)
  const [editingFeature, setEditingFeature] = useState(false)
  const [editForm, setEditForm] = useState({ label: '', square_width: 1, square_height: 1 })
  const [editError, setEditError] = useState('')
  const [removing, setRemoving] = useState(false)

  const fetchYard = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/yards/${id}`)
      if (!res.ok) throw new Error('Yard not found')
      setYard(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load yard')
    }
  }, [id])

  const fetchAvailableBeds = useCallback(async () => {
    try {
      const res = await apiFetch('/api/containers')
      if (!res.ok) return
      const all: ContainerOption[] = await res.json()
      setAvailableBeds(all.filter(c => c.type === 'grid_bed'))
    } catch {
      // non-critical
    }
  }, [])

  useEffect(() => {
    if (id) {
      Promise.all([fetchYard(), fetchAvailableBeds()]).finally(() => setLoading(false))
    }
  }, [id, fetchYard, fetchAvailableBeds])

  async function handleDelete() {
    if (!confirm('Delete this yard? Beds placed here will not be deleted, just un-placed.')) return
    setDeleting(true)
    try {
      const res = await apiFetch(`/api/yards/${id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to delete')
      }
      navigate('/yards')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
      setDeleting(false)
    }
  }

  function getObjectAt(x: number, y: number): YardObj | undefined {
    return yard?.objects.find(o => {
      const inX = x >= o.square_x && x < o.square_x + o.square_width
      const inY = y >= o.square_y && y < o.square_y + o.square_height
      return inX && inY
    })
  }

  function handleSquareClick(x: number, y: number) {
    if (moving) {
      submitMove(x, y)
      return
    }

    const obj = getObjectAt(x, y)

    if (mode === 'display') {
      if (!obj) return
      if (obj.object_type === 'bed' && obj.container_id) {
        navigate(`/containers/${obj.container_id}`)
      } else {
        setSelectedObject(obj)
        setEditingFeature(false)
        setEditError('')
      }
      return
    }

    if (obj) {
      setSelectedObject(obj)
      setEditingFeature(false)
      setEditError('')
    } else {
      setChooser({ x, y })
      setChooserMode('choose')
      setChooserError('')
      setBedForm({ containerId: '' })
      setFeatureForm({ object_type: 'path', label: '', square_width: 1, square_height: 1 })
    }
  }

  function startMove() {
    if (!selectedObject) return
    setMoving(selectedObject)
    setSelectedObject(null)
    setMoveError('')
  }

  function cancelMove() {
    setMoving(null)
    setMoveError('')
  }

  async function submitMove(x: number, y: number) {
    if (!moving) return
    setMoveSubmitting(true)
    setMoveError('')
    try {
      const res = await apiFetch(`/api/yards/${id}/objects/${moving.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ square_x: x, square_y: y }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to move')
      }
      setMoving(null)
      await fetchYard()
    } catch (err: unknown) {
      setMoveError(err instanceof Error ? err.message : 'Failed to move')
    } finally {
      setMoveSubmitting(false)
    }
  }

  function closeChooser() {
    setChooser(null)
    setChooserMode('choose')
    setChooserError('')
  }

  async function submitPlaceBed(e: React.FormEvent) {
    e.preventDefault()
    if (!chooser || !bedForm.containerId) return
    setSubmitting(true)
    setChooserError('')
    try {
      const res = await apiFetch(`/api/yards/${id}/objects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          object_type: 'bed',
          container_id: bedForm.containerId,
          square_x: chooser.x,
          square_y: chooser.y,
        }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to place bed')
      }
      closeChooser()
      await Promise.all([fetchYard(), fetchAvailableBeds()])
    } catch (err: unknown) {
      setChooserError(err instanceof Error ? err.message : 'Failed to place bed')
    } finally {
      setSubmitting(false)
    }
  }

  async function submitAddFeature(e: React.FormEvent) {
    e.preventDefault()
    if (!chooser) return
    setSubmitting(true)
    setChooserError('')
    try {
      const res = await apiFetch(`/api/yards/${id}/objects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          object_type: featureForm.object_type,
          label: featureForm.label || null,
          square_x: chooser.x,
          square_y: chooser.y,
          square_width: featureForm.square_width,
          square_height: featureForm.square_height,
        }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to add feature')
      }
      closeChooser()
      await fetchYard()
    } catch (err: unknown) {
      setChooserError(err instanceof Error ? err.message : 'Failed to add feature')
    } finally {
      setSubmitting(false)
    }
  }

  function startEditFeature() {
    if (!selectedObject) return
    setEditForm({
      label: selectedObject.label || '',
      square_width: selectedObject.square_width,
      square_height: selectedObject.square_height,
    })
    setEditError('')
    setEditingFeature(true)
  }

  async function submitEditFeature(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedObject) return
    setSubmitting(true)
    setEditError('')
    try {
      const res = await apiFetch(`/api/yards/${id}/objects/${selectedObject.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          label: editForm.label || null,
          square_width: editForm.square_width,
          square_height: editForm.square_height,
        }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to update')
      }
      setSelectedObject(null)
      setEditingFeature(false)
      await fetchYard()
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : 'Failed to update')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRemoveObject() {
    if (!selectedObject) return
    setRemoving(true)
    try {
      const res = await apiFetch(`/api/yards/${id}/objects/${selectedObject.id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to remove')
      }
      setSelectedObject(null)
      await Promise.all([fetchYard(), fetchAvailableBeds()])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to remove')
    } finally {
      setRemoving(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading yard...</p>
      </div>
    )
  }

  if (error || !yard) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Yard not found'}</div>
        <Link to="/yards" className="btn btn-outline-dark">← Back to Yards</Link>
      </div>
    )
  }

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to="/yards" className="back-link">← Back to Yards</Link>
        <div className="page-header-row">
          <div>
            <h2>{yard.name}</h2>
            <span className="text-muted">{yard.width}×{yard.height} squares</span>
          </div>
          <div className="page-header-actions">
            <button
              onClick={() => {
                setMode(m => m === 'display' ? 'planning' : 'display')
                cancelMove()
                setChooser(null)
                setSelectedObject(null)
              }}
              className="btn btn-outline-dark btn-sm"
            >
              {mode === 'display' ? '🔧 Planning Mode' : '✅ Done Planning'}
            </button>
            <Link to={`/yards/${id}/edit`} className="btn btn-outline-dark btn-sm">
              Edit
            </Link>
            <button onClick={handleDelete} className="btn btn-danger btn-sm" disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </div>

      <div className="detail-section">
        <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
          {mode === 'planning'
            ? 'Click an empty square to place a bed or add a feature. Click a filled square to view, move, or edit it.'
            : 'Click a bed to open it. Switch to Planning Mode to add, move, or edit items.'}
        </p>

        {moving && (
          <div className="yard-move-banner">
            <span>Click a square to move <strong>{objectDisplayName(moving)}</strong> here.</span>
            {moveError && <span className="yard-move-error">{moveError}</span>}
            <button className="btn btn-outline-dark btn-sm" onClick={cancelMove} disabled={moveSubmitting}>
              Cancel
            </button>
          </div>
        )}

        <div
          className={`yard-grid-wrapper ${mode === 'display' ? 'display-mode' : 'planning-mode'}`}
          style={{ '--grid-cols': yard.width } as React.CSSProperties}
        >
          <div className="grid-header-row">
            <div className="grid-corner" />
            {Array.from({ length: yard.width }).map((_, x) => (
              <div key={x} className="grid-col-label">{x + 1}</div>
            ))}
          </div>
          {Array.from({ length: yard.height }).map((_, y) => (
            <div key={y} className="grid-row">
              <div className="grid-row-label">{rowLabel(y)}</div>
              {Array.from({ length: yard.width }).map((_, x) => {
                const obj = getObjectAt(x, y)
                const isMulti = obj ? obj.square_width > 1 || obj.square_height > 1 : false
                const isEdgeTop = obj && y === obj.square_y
                const isEdgeBottom = obj && y === obj.square_y + obj.square_height - 1
                const isEdgeLeft = obj && x === obj.square_x
                const isEdgeRight = obj && x === obj.square_x + obj.square_width - 1
                const showContent = obj && x === obj.square_x && y === obj.square_y

                return (
                  <div
                    key={x}
                    className={[
                      'grid-square',
                      obj ? `yard-obj-${obj.object_type}` : 'yard-empty',
                      isMulti ? 'is-multi-sq' : '',
                      isMulti && isEdgeTop ? 'multi-edge-top' : '',
                      isMulti && isEdgeBottom ? 'multi-edge-bottom' : '',
                      isMulti && isEdgeLeft ? 'multi-edge-left' : '',
                      isMulti && isEdgeRight ? 'multi-edge-right' : '',
                    ].filter(Boolean).join(' ')}
                    onClick={() => handleSquareClick(x, y)}
                    title={obj ? objectDisplayName(obj) : `${rowLabel(y)}${x + 1} — empty`}
                  >
                    {showContent && (
                      <>
                        <span className="yard-obj-icon">{OBJECT_ICONS[obj.object_type] || '📍'}</span>
                        <span className="yard-obj-label">{objectDisplayName(obj)}</span>
                      </>
                    )}
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        <div className="grid-legend">
          <span className="legend-item"><span className="legend-swatch fallow" /> Empty</span>
          <span className="legend-item"><span className="legend-swatch yard-obj-bed" /> Bed</span>
          <span className="legend-item"><span className="legend-swatch yard-obj-path" /> Path</span>
          <span className="legend-item"><span className="legend-swatch yard-obj-mulch" /> Mulch</span>
          <span className="legend-item"><span className="legend-swatch yard-obj-building" /> Building</span>
          <span className="legend-item"><span className="legend-swatch yard-obj-tree" /> Tree</span>
          <span className="legend-item"><span className="legend-swatch yard-obj-water" /> Water</span>
        </div>
      </div>

      {/* Empty-square chooser modal */}
      {chooser && (
        <div className="modal-overlay" onClick={closeChooser}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{rowLabel(chooser.y)}{chooser.x + 1}</h3>
              <button className="modal-close" onClick={closeChooser}>✕</button>
            </div>

            {chooserMode === 'choose' && (
              <div className="square-chooser-actions">
                <button className="square-chooser-btn" onClick={() => setChooserMode('bed')}>
                  <span className="chooser-icon">🌿</span>
                  <span className="chooser-label">Place a Bed</span>
                  <span className="chooser-desc">Position one of your existing garden beds here</span>
                </button>
                <button className="square-chooser-btn" onClick={() => setChooserMode('feature')}>
                  <span className="chooser-icon">🏠</span>
                  <span className="chooser-label">Add a Feature</span>
                  <span className="chooser-desc">Mark this area as path, mulch, a building, a tree, etc.</span>
                </button>
              </div>
            )}

            {chooserMode === 'bed' && (
              <form onSubmit={submitPlaceBed}>
                {availableBeds.filter(b => !b.is_placed).length === 0 ? (
                  <p className="text-muted" style={{ padding: 'var(--space-2)' }}>
                    All your garden beds are already placed in a yard, or you have none yet.{' '}
                    <Link to="/containers/new">Add one</Link>
                  </p>
                ) : (
                  <div className="form-group">
                    <label className="form-label">Bed *</label>
                    <select
                      className="form-input"
                      value={bedForm.containerId}
                      onChange={(e) => setBedForm({ containerId: e.target.value ? Number(e.target.value) : '' })}
                      required
                    >
                      <option value="">Select a bed…</option>
                      {availableBeds.filter(b => !b.is_placed).map(b => (
                        <option key={b.id} value={b.id}>
                          {b.name} ({b.width}×{b.height})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {chooserError && <div className="form-message error">{chooserError}</div>}

                <div className="modal-actions">
                  <button type="button" className="btn btn-outline-dark" onClick={() => setChooserMode('choose')}>
                    ← Back
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={!bedForm.containerId || submitting}>
                    {submitting ? 'Placing...' : 'Place Bed'}
                  </button>
                </div>
              </form>
            )}

            {chooserMode === 'feature' && (
              <form onSubmit={submitAddFeature}>
                <div className="form-group">
                  <label className="form-label">Type *</label>
                  <div className="category-filter-chips">
                    {FEATURE_TYPES.map(f => (
                      <button
                        key={f.value}
                        type="button"
                        className={`chip ${featureForm.object_type === f.value ? 'active' : ''}`}
                        onClick={() => setFeatureForm({ ...featureForm, object_type: f.value })}
                      >
                        {f.icon} {f.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Width (squares)</label>
                    <input
                      type="number"
                      className="form-input"
                      min={1}
                      max={Math.max(1, yard.width - chooser.x)}
                      value={featureForm.square_width}
                      onChange={(e) => setFeatureForm({ ...featureForm, square_width: Number(e.target.value) || 1 })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Height (squares)</label>
                    <input
                      type="number"
                      className="form-input"
                      min={1}
                      max={Math.max(1, yard.height - chooser.y)}
                      value={featureForm.square_height}
                      onChange={(e) => setFeatureForm({ ...featureForm, square_height: Number(e.target.value) || 1 })}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Label (optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g., Oak tree, Toolshed"
                    value={featureForm.label}
                    onChange={(e) => setFeatureForm({ ...featureForm, label: e.target.value })}
                  />
                </div>

                {chooserError && <div className="form-message error">{chooserError}</div>}

                <div className="modal-actions">
                  <button type="button" className="btn btn-outline-dark" onClick={() => setChooserMode('choose')}>
                    ← Back
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Adding...' : 'Add Feature'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Occupied-square detail modal */}
      {selectedObject && (
        <div className="modal-overlay" onClick={() => setSelectedObject(null)}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {OBJECT_ICONS[selectedObject.object_type] || '📍'} {objectDisplayName(selectedObject)}
              </h3>
              <button className="modal-close" onClick={() => setSelectedObject(null)}>✕</button>
            </div>

            {editingFeature ? (
              <form onSubmit={submitEditFeature}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Width (squares)</label>
                    <input
                      type="number"
                      className="form-input"
                      min={1}
                      value={editForm.square_width}
                      onChange={(e) => setEditForm({ ...editForm, square_width: Number(e.target.value) || 1 })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Height (squares)</label>
                    <input
                      type="number"
                      className="form-input"
                      min={1}
                      value={editForm.square_height}
                      onChange={(e) => setEditForm({ ...editForm, square_height: Number(e.target.value) || 1 })}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Label</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editForm.label}
                    onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                  />
                </div>

                {editError && <div className="form-message error">{editError}</div>}

                <div className="modal-actions">
                  <button type="button" className="btn btn-outline-dark" onClick={() => setEditingFeature(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            ) : (
              <>
                <div className="detail-grid compact">
                  <div className="detail-item">
                    <span className="detail-label">Position</span>
                    <span className="detail-value">
                      {rowLabel(selectedObject.square_y)}{selectedObject.square_x + 1}
                      {(selectedObject.square_width > 1 || selectedObject.square_height > 1)
                        ? ` (${selectedObject.square_width}×${selectedObject.square_height})`
                        : ''}
                    </span>
                  </div>
                </div>

                {mode === 'planning' ? (
                  <div className="modal-actions">
                    <button className="btn btn-outline-dark" onClick={startMove}>
                      ↔️ Move
                    </button>
                    {selectedObject.object_type === 'bed' ? (
                      <Link to={`/containers/${selectedObject.container_id}`} className="btn btn-outline-dark">
                        View Bed
                      </Link>
                    ) : (
                      <button className="btn btn-outline-dark" onClick={startEditFeature}>
                        ✏️ Edit
                      </button>
                    )}
                    <button className="btn btn-danger" onClick={handleRemoveObject} disabled={removing}>
                      {removing ? 'Removing...' : 'Remove from Yard'}
                    </button>
                  </div>
                ) : (
                  <div className="modal-actions">
                    <button className="btn btn-outline-dark" onClick={() => setSelectedObject(null)}>
                      Close
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
