import { useEffect, useState } from 'react'
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [supportMenu, setSupportMenu] = useState<{ x: number; y: number } | null>(null)

  useEffect(() => {
    if (id) fetchContainer()
  }, [id])

  async function fetchContainer() {
    try {
      const res = await fetch(`/api/containers/${id}`)
      if (!res.ok) throw new Error('Container not found')
      setContainer(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load container')
    } finally {
      setLoading(false)
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
    return container?.square_supports.find(s => s.square_x === x && s.square_y === y)
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

      {/* Irrigation Info */}
      {container.irrigation_type && (
        <div className="detail-section">
          <h3>💧 Irrigation</h3>
          <div className="irrigation-info">
            <span>Type: <strong>{container.irrigation_type}</strong></span>
            {container.irrigation_duration_minutes && (
              <span>Duration: <strong>{container.irrigation_duration_minutes} min</strong></span>
            )}
            {container.irrigation_frequency && (
              <span>Frequency: <strong>{container.irrigation_frequency.replace('_', ' ')}</strong></span>
            )}
          </div>
        </div>
      )}

      {/* Grid Bed View */}
      {container.type === 'grid_bed' && (
        <div className="detail-section">
          <h3>Grid Layout</h3>
          <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
            Click a square to add/remove support structures.
          </p>
          <div className="grid-container">
            {/* Column headers */}
            <div className="grid-header-row">
              <div className="grid-corner" />
              {Array.from({ length: container.width || 0 }).map((_, x) => (
                <div key={x} className="grid-col-label">{x + 1}</div>
              ))}
            </div>
            {/* Grid rows */}
            {Array.from({ length: container.height || 0 }).map((_, y) => (
              <div key={y} className="grid-row">
                <div className="grid-row-label">{ROW_LABELS[y]}</div>
                {Array.from({ length: container.width || 0 }).map((_, x) => {
                  const support = getSupportAt(x, y)
                  const isMenuOpen = supportMenu?.x === x && supportMenu?.y === y
                  return (
                    <div
                      key={x}
                      className={`grid-square fallow ${support ? 'has-support' : ''} ${isMenuOpen ? 'active' : ''}`}
                      onClick={() => setSupportMenu(isMenuOpen ? null : { x, y })}
                      title={`${ROW_LABELS[y]}${x + 1}${support ? ` (${support.support_type})` : ''}`}
                    >
                      {support && (
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
        </div>
      )}

      {/* Tower View */}
      {container.type === 'tower' && (
        <div className="detail-section">
          <h3>Tower Layout</h3>
          <div className="tower-container">
            {Array.from({ length: container.levels || 0 }).map((_, level) => (
              <div key={level} className="tower-level">
                <div className="tower-level-label">Level {level + 1}</div>
                <div className="tower-pockets">
                  {Array.from({ length: container.pockets_per_level || 0 }).map((_, pocket) => (
                    <div key={pocket} className="tower-pocket fallow">
                      <span className="pocket-label">{pocket + 1}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
