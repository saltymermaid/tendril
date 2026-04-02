import { useEffect, useState, useCallback } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface SquareSupport {
  id: number
  container_id: number
  square_x: number
  square_y: number
  support_type: string
}

interface ContainerDetail {
  id: number
  user_id: number
  name: string
  type: string
  location_description: string | null
  width: number | null
  height: number | null
  levels: number | null
  pockets_per_level: number | null
  irrigation_type: string | null
  irrigation_duration_minutes: number | null
  irrigation_frequency: string | null
  square_supports: SquareSupport[]
}

interface PlantingData {
  id: number
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
  variety_name: string | null
  category_name: string | null
  category_color: string | null
}

interface Variety {
  id: number
  name: string
  category_id: number
  category_name: string | null
  category_color: string | null
}

interface Category {
  id: number
  name: string
  color: string
}

const SUPPORT_ICONS: Record<string, string> = {
  trellis: '🪜',
  cage: '🔲',
  pole: '🪵',
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

export function ContainerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [container, setContainer] = useState<ContainerDetail | null>(null)
  const [plantings, setPlantings] = useState<PlantingData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  // Support menu state
  const [supportMenu, setSupportMenu] = useState<{ x: number; y: number } | null>(null)

  // Planting modal state
  const [plantingModal, setPlantingModal] = useState<{
    x: number
    y: number
    towerLevel?: number
  } | null>(null)
  const [varieties, setVarieties] = useState<Variety[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [varietySearch, setVarietySearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [selectedVariety, setSelectedVariety] = useState<number | null>(null)
  const [plantingForm, setPlantingForm] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    planting_method: '' as string,
    quantity: '' as string,
    square_width: 1,
    square_height: 1,
  })
  const [plantingError, setPlantingError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Selected planting for detail view
  const [selectedPlanting, setSelectedPlanting] = useState<PlantingData | null>(null)

  const fetchContainer = useCallback(async () => {
    try {
      const res = await fetch(`/api/containers/${id}`)
      if (!res.ok) throw new Error('Container not found')
      setContainer(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load container')
    }
  }, [id])

  const fetchPlantings = useCallback(async () => {
    try {
      const res = await fetch(`/api/plantings/by-container/${id}`)
      if (!res.ok) throw new Error('Failed to load plantings')
      setPlantings(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load plantings')
    }
  }, [id])

  useEffect(() => {
    if (id) {
      Promise.all([fetchContainer(), fetchPlantings()]).finally(() => setLoading(false))
    }
  }, [id, fetchContainer, fetchPlantings])

  async function fetchVarietiesAndCategories() {
    try {
      const [varRes, catRes] = await Promise.all([
        fetch('/api/varieties'),
        fetch('/api/categories'),
      ])
      if (varRes.ok) setVarieties(await varRes.json())
      if (catRes.ok) setCategories(await catRes.json())
    } catch {
      // Non-critical
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this container? This cannot be undone.')) return
    setDeleting(true)
    try {
      const res = await fetch(`/api/containers/${id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to delete')
      }
      navigate('/containers')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
      setDeleting(false)
    }
  }

  async function setSupport(x: number, y: number, supportType: string) {
    try {
      const res = await fetch(`/api/containers/${id}/squares/${x}/${y}/support`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ support_type: supportType }),
      })
      if (!res.ok) throw new Error('Failed to set support')
      setSupportMenu(null)
      fetchContainer()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to set support')
    }
  }

  async function removeSupport(x: number, y: number) {
    try {
      await fetch(`/api/containers/${id}/squares/${x}/${y}/support`, { method: 'DELETE' })
      setSupportMenu(null)
      fetchContainer()
    } catch {
      setError('Failed to remove support')
    }
  }

  function getSupportAt(x: number, y: number): SquareSupport | undefined {
    return container?.square_supports.find((s: SquareSupport) => s.square_x === x && s.square_y === y)
  }

  function getPlantingAt(x: number, y: number): PlantingData | undefined {
    const today = new Date().toISOString().split('T')[0]
    return plantings.find((p: PlantingData) => {
      const inX = x >= p.square_x && x < p.square_x + p.square_width
      const inY = y >= p.square_y && y < p.square_y + p.square_height
      const active = p.start_date <= today && p.end_date > today
      return inX && inY && active
    })
  }

  function getPlantingAtLevel(level: number, pocket: number): PlantingData | undefined {
    const today = new Date().toISOString().split('T')[0]
    return plantings.find((p: PlantingData) => {
      return p.tower_level === level && p.square_x === pocket &&
        p.start_date <= today && p.end_date > today
    })
  }

  function isPlantingOrigin(p: PlantingData, x: number, y: number): boolean {
    return p.square_x === x && p.square_y === y
  }

  function openPlantingModal(x: number, y: number, towerLevel?: number) {
    setPlantingModal({ x, y, towerLevel })
    setPlantingError('')
    setSelectedVariety(null)
    setVarietySearch('')
    setSelectedCategory(null)
    setPlantingForm({
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
      planting_method: '',
      quantity: '',
      square_width: 1,
      square_height: 1,
    })
    fetchVarietiesAndCategories()
  }

  async function handleCreatePlanting(e: React.FormEvent) {
    e.preventDefault()
    if (!plantingModal || !selectedVariety) return

    setSubmitting(true)
    setPlantingError('')

    try {
      const body: Record<string, unknown> = {
        container_id: Number(id),
        variety_id: selectedVariety,
        square_x: plantingModal.x,
        square_y: plantingModal.y,
        square_width: plantingForm.square_width,
        square_height: plantingForm.square_height,
        start_date: plantingForm.start_date,
        end_date: plantingForm.end_date,
      }

      if (plantingModal.towerLevel !== undefined) {
        body.tower_level = plantingModal.towerLevel
      }
      if (plantingForm.planting_method) {
        body.planting_method = plantingForm.planting_method
      }
      if (plantingForm.quantity) {
        body.quantity = Number(plantingForm.quantity)
      }

      const res = await fetch('/api/plantings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to create planting')
      }

      setPlantingModal(null)
      fetchPlantings()
    } catch (err: unknown) {
      setPlantingError(err instanceof Error ? err.message : 'Failed to create planting')
    } finally {
      setSubmitting(false)
    }
  }

  const filteredVarieties = varieties.filter((v: Variety) => {
    const matchesSearch = !varietySearch ||
      v.name.toLowerCase().includes(varietySearch.toLowerCase()) ||
      (v.category_name || '').toLowerCase().includes(varietySearch.toLowerCase())
    const matchesCategory = !selectedCategory || v.category_id === selectedCategory
    return matchesSearch && matchesCategory
  })

  function handleSquareClick(x: number, y: number) {
    const planting = getPlantingAt(x, y)
    if (planting) {
      setSelectedPlanting(planting)
      setSupportMenu(null)
    } else {
      openPlantingModal(x, y)
    }
  }

  function handleSquareRightClick(e: React.MouseEvent, x: number, y: number) {
    e.preventDefault()
    setSupportMenu(supportMenu?.x === x && supportMenu?.y === y ? null : { x, y })
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading container...</p>
      </div>
    )
  }

  if (error || !container) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Container not found'}</div>
        <Link to="/containers" className="btn btn-outline-dark">← Back to Containers</Link>
      </div>
    )
  }

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to="/containers" className="back-link">← Back to Containers</Link>
        <div className="page-header-row">
          <div>
            <h2>{container.name}</h2>
            <span className="text-muted">
              {container.type === 'grid_bed'
                ? `${container.width}×${container.height} Garden Bed`
                : `${container.levels}-Level Tower`}
              {container.location_description && ` · 📍 ${container.location_description}`}
            </span>
          </div>
          <div className="page-header-actions">
            <Link to={`/containers/${id}/edit`} className="btn btn-outline-dark btn-sm">
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

      {/* Container Info */}
      <div className="container-info-grid">
        {container.type === 'grid_bed' && (
          <div className="container-info-item">
            <div className="info-label">Dimensions</div>
            <div className="info-value">{container.width} × {container.height} squares</div>
          </div>
        )}
        {container.type === 'tower' && (
          <>
            <div className="container-info-item">
              <div className="info-label">Levels</div>
              <div className="info-value">{container.levels}</div>
            </div>
            <div className="container-info-item">
              <div className="info-label">Pockets per Level</div>
              <div className="info-value">{container.pockets_per_level}</div>
            </div>
          </>
        )}
        {container.irrigation_type && (
          <div className="container-info-item">
            <div className="info-label">Irrigation</div>
            <div className="info-value">
              💧 {container.irrigation_type}
              {container.irrigation_frequency && ` · ${container.irrigation_frequency}`}
            </div>
          </div>
        )}
        <div className="container-info-item">
          <div className="info-label">Active Plantings</div>
          <div className="info-value">{plantings.filter((p: PlantingData) => p.status !== 'complete').length}</div>
        </div>
      </div>

      {/* Grid Bed View */}
      {container.type === 'grid_bed' && (
        <div className="detail-section">
          <h3>Garden Bed</h3>
          <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
            Click a square to plant. Right-click for support structures.
          </p>
          <div className="grid-bed-wrapper">
            <div className="grid-header-row">
              <div className="grid-corner" />
              {Array.from({ length: container.width || 0 }).map((_, x) => (
                <div key={x} className="grid-col-label">{x + 1}</div>
              ))}
            </div>
            {Array.from({ length: container.height || 0 }).map((_, y) => (
              <div key={y} className="grid-row">
                <div className="grid-row-label">{ROW_LABELS[y]}</div>
                {Array.from({ length: container.width || 0 }).map((_, x) => {
                  const support = getSupportAt(x, y)
                  const planting = getPlantingAt(x, y)
                  const isMenuOpen = supportMenu?.x === x && supportMenu?.y === y
                  const isOrigin = planting ? isPlantingOrigin(planting, x, y) : false

                  return (
                    <div
                      key={x}
                      className={[
                        'grid-square',
                        support ? 'has-support' : '',
                        planting ? 'planted' : 'fallow',
                        planting?.status === 'not_started' ? 'not-started' : '',
                        planting?.status === 'in_progress' ? 'in-progress' : '',
                        planting?.status === 'complete' ? 'complete' : '',
                        isMenuOpen ? 'active' : '',
                      ].filter(Boolean).join(' ')}
                      style={planting ? { backgroundColor: (planting.category_color || '#86efac') + '40', borderColor: planting.category_color || undefined } : undefined}
                      onClick={() => handleSquareClick(x, y)}
                      onContextMenu={(e) => handleSquareRightClick(e, x, y)}
                      title={
                        planting
                          ? `${planting.variety_name} (${planting.status})`
                          : `${ROW_LABELS[y]}${x + 1}${support ? ` — ${support.support_type}` : ' — empty'}`
                      }
                    >
                      {planting && isOrigin && (
                        <span className="square-variety-name">
                          {planting.variety_name?.substring(0, 6)}
                        </span>
                      )}
                      {!planting && support && (
                        <span className="support-icon">{SUPPORT_ICONS[support.support_type] || '🔧'}</span>
                      )}
                      {isMenuOpen && (
                        <div className="support-menu" onClick={(e) => e.stopPropagation()}>
                          <div className="support-menu-title">{ROW_LABELS[y]}{x + 1}</div>
                          <button onClick={() => setSupport(x, y, 'trellis')}>🪜 Trellis</button>
                          <button onClick={() => setSupport(x, y, 'cage')}>🔲 Cage</button>
                          <button onClick={() => setSupport(x, y, 'pole')}>🪵 Pole</button>
                          {support && (
                            <button onClick={() => removeSupport(x, y)} className="remove-support">
                              ✕ Remove
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>

          <div className="grid-legend">
            <span className="legend-item"><span className="legend-swatch fallow" /> Empty</span>
            <span className="legend-item"><span className="legend-swatch not-started" /> Planned</span>
            <span className="legend-item"><span className="legend-swatch in-progress" /> Growing</span>
            <span className="legend-item"><span className="legend-swatch complete" /> Complete</span>
          </div>
        </div>
      )}

      {/* Tower View */}
      {container.type === 'tower' && (
        <div className="detail-section">
          <h3>Tower Layout</h3>
          <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
            Click a pocket to plant.
          </p>
          <div className="tower-levels">
            {Array.from({ length: container.levels || 0 }).map((_, level) => (
              <div key={level} className="tower-level">
                <h4>Level {level + 1}</h4>
                <div className="tower-pockets">
                  {Array.from({ length: container.pockets_per_level || 0 }).map((_, pocket) => {
                    const planting = getPlantingAtLevel(level, pocket)
                    return (
                      <div
                        key={pocket}
                        className={[
                          'tower-pocket',
                          planting ? 'planted' : 'fallow',
                          planting?.status === 'not_started' ? 'not-started' : '',
                          planting?.status === 'in_progress' ? 'in-progress' : '',
                        ].filter(Boolean).join(' ')}
                        style={planting ? { backgroundColor: (planting.category_color || '#86efac') + '40', borderColor: planting.category_color || undefined } : undefined}
                        onClick={() => {
                          if (planting) {
                            setSelectedPlanting(planting)
                          } else {
                            openPlantingModal(pocket, 0, level)
                          }
                        }}
                        title={planting ? planting.variety_name || '' : `Pocket ${pocket + 1}`}
                      >
                        {planting ? (
                          <span className="pocket-variety">{planting.variety_name?.substring(0, 3)}</span>
                        ) : (
                          <span className="pocket-label">{pocket + 1}</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plantings List */}
      {plantings.length > 0 && (
        <div className="detail-section">
          <h3>All Plantings ({plantings.length})</h3>
          <div className="plantings-list">
            {plantings.map((p: PlantingData) => (
              <div
                key={p.id}
                className={`planting-list-item ${p.status}`}
                onClick={() => setSelectedPlanting(p)}
              >
                <div
                  className="planting-color-dot"
                  style={{ backgroundColor: p.category_color || '#ccc' }}
                />
                <div className="planting-list-info">
                  <strong>{p.variety_name}</strong>
                  <span className="text-muted">
                    {p.category_name} · {ROW_LABELS[p.square_y]}{p.square_x + 1}
                    {p.square_width > 1 || p.square_height > 1
                      ? ` (${p.square_width}×${p.square_height})`
                      : ''}
                  </span>
                </div>
                <div className="planting-list-dates">
                  <span>{p.start_date} → {p.end_date}</span>
                  <span className={`status-badge ${p.status}`}>
                    {p.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Planting Creation Modal */}
      {plantingModal && (
        <div className="modal-overlay" onClick={() => setPlantingModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                🌱 New Planting —{' '}
                {plantingModal.towerLevel !== undefined
                  ? `Level ${plantingModal.towerLevel + 1}, Pocket ${plantingModal.x + 1}`
                  : `${ROW_LABELS[plantingModal.y]}${plantingModal.x + 1}`}
              </h3>
              <button className="modal-close" onClick={() => setPlantingModal(null)}>✕</button>
            </div>

            <form onSubmit={handleCreatePlanting}>
              <div className="form-group">
                <label className="form-label">Variety *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Search varieties..."
                  value={varietySearch}
                  onChange={(e) => setVarietySearch(e.target.value)}
                />
                {categories.length > 0 && (
                  <div className="category-filter-chips">
                    <button
                      type="button"
                      className={`chip ${!selectedCategory ? 'active' : ''}`}
                      onClick={() => setSelectedCategory(null)}
                    >
                      All
                    </button>
                    {categories.map((c: Category) => (
                      <button
                        key={c.id}
                        type="button"
                        className={`chip ${selectedCategory === c.id ? 'active' : ''}`}
                        style={selectedCategory === c.id ? { backgroundColor: c.color, color: '#fff' } : undefined}
                        onClick={() => setSelectedCategory(c.id)}
                      >
                        {c.name}
                      </button>
                    ))}
                  </div>
                )}
                <div className="variety-picker-list">
                  {filteredVarieties.length === 0 ? (
                    <p className="text-muted" style={{ padding: 'var(--space-2)' }}>
                      No varieties found. <Link to="/catalog/varieties/new">Add one</Link>
                    </p>
                  ) : (
                    filteredVarieties.map((v: Variety) => (
                      <div
                        key={v.id}
                        className={`variety-picker-item ${selectedVariety === v.id ? 'selected' : ''}`}
                        onClick={() => setSelectedVariety(v.id)}
                      >
                        <span
                          className="variety-picker-dot"
                          style={{ backgroundColor: v.category_color || '#ccc' }}
                        />
                        <span className="variety-picker-name">{v.name}</span>
                        <span className="variety-picker-category">{v.category_name}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Start Date *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={plantingForm.start_date}
                    onChange={(e) => setPlantingForm({ ...plantingForm, start_date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Date *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={plantingForm.end_date}
                    onChange={(e) => setPlantingForm({ ...plantingForm, end_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              {container.type === 'grid_bed' && (
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Width (squares)</label>
                    <select
                      className="form-input"
                      value={plantingForm.square_width}
                      onChange={(e) => setPlantingForm({ ...plantingForm, square_width: Number(e.target.value) })}
                    >
                      <option value={1}>1</option>
                      <option value={2}>2</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Height (squares)</label>
                    <select
                      className="form-input"
                      value={plantingForm.square_height}
                      onChange={(e) => setPlantingForm({ ...plantingForm, square_height: Number(e.target.value) })}
                    >
                      <option value={1}>1</option>
                      <option value={2}>2</option>
                    </select>
                  </div>
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Method</label>
                  <select
                    className="form-input"
                    value={plantingForm.planting_method}
                    onChange={(e) => setPlantingForm({ ...plantingForm, planting_method: e.target.value })}
                  >
                    <option value="">—</option>
                    <option value="direct_sow">Direct Sow</option>
                    <option value="transplant">Transplant</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Quantity</label>
                  <input
                    type="number"
                    className="form-input"
                    min="1"
                    value={plantingForm.quantity}
                    onChange={(e) => setPlantingForm({ ...plantingForm, quantity: e.target.value })}
                    placeholder="Optional"
                  />
                </div>
              </div>

              {plantingError && <div className="form-message error">{plantingError}</div>}

              <div className="modal-actions">
                <button type="button" className="btn btn-outline-dark" onClick={() => setPlantingModal(null)}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!selectedVariety || !plantingForm.end_date || submitting}
                >
                  {submitting ? 'Planting...' : '🌱 Plant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Planting Detail Modal */}
      {selectedPlanting && (
        <div className="modal-overlay" onClick={() => setSelectedPlanting(null)}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <span
                  className="planting-color-dot inline"
                  style={{ backgroundColor: selectedPlanting.category_color || '#ccc' }}
                />
                {selectedPlanting.variety_name}
              </h3>
              <button className="modal-close" onClick={() => setSelectedPlanting(null)}>✕</button>
            </div>

            <div className="planting-detail-body">
              <div className="detail-grid compact">
                <div className="detail-item">
                  <span className="detail-label">Category</span>
                  <span className="detail-value">{selectedPlanting.category_name}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Position</span>
                  <span className="detail-value">
                    {selectedPlanting.tower_level !== null
                      ? `Level ${selectedPlanting.tower_level + 1}, Pocket ${selectedPlanting.square_x + 1}`
                      : `${ROW_LABELS[selectedPlanting.square_y]}${selectedPlanting.square_x + 1}`}
                    {selectedPlanting.square_width > 1 || selectedPlanting.square_height > 1
                      ? ` (${selectedPlanting.square_width}×${selectedPlanting.square_height})`
                      : ''}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Status</span>
                  <span className={`status-badge ${selectedPlanting.status}`}>
                    {selectedPlanting.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Dates</span>
                  <span className="detail-value">{selectedPlanting.start_date} → {selectedPlanting.end_date}</span>
                </div>
                {selectedPlanting.planting_method && (
                  <div className="detail-item">
                    <span className="detail-label">Method</span>
                    <span className="detail-value">{selectedPlanting.planting_method.replace('_', ' ')}</span>
                  </div>
                )}
                {selectedPlanting.quantity && (
                  <div className="detail-item">
                    <span className="detail-label">Quantity</span>
                    <span className="detail-value">{selectedPlanting.quantity}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-actions">
              <Link
                to={`/plantings/${selectedPlanting.id}`}
                className="btn btn-outline-dark"
              >
                View Details
              </Link>
              <button className="btn btn-primary" onClick={() => setSelectedPlanting(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
