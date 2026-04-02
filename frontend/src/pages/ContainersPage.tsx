import { apiFetch } from "../lib/api"
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface Container {
  id: number
  name: string
  type: string
  location_description: string | null
  width: number | null
  height: number | null
  levels: number | null
  pockets_per_level: number | null
  irrigation_type: string | null
}

export function ContainersPage() {
  const [containers, setContainers] = useState<Container[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchContainers()
  }, [])

  async function fetchContainers() {
    try {
      const res = await apiFetch('/api/containers')
      if (!res.ok) throw new Error('Failed to load containers')
      setContainers(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load containers')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading containers...</p>
      </div>
    )
  }

  const gridBeds = containers.filter(c => c.type === 'grid_bed')
  const towers = containers.filter(c => c.type === 'tower')

  return (
    <div className="catalog-page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2>Containers</h2>
            <p className="text-muted">Manage your garden beds and towers</p>
          </div>
          <Link to="/containers/new" className="btn btn-primary">
            + Add Container
          </Link>
        </div>
      </div>

      {error && <div className="form-message error">{error}</div>}

      {/* Grid Beds */}
      {gridBeds.length > 0 && (
        <div className="detail-section">
          <h3>🌿 Garden Beds</h3>
          <div className="container-list">
            {gridBeds.map((c) => (
              <Link key={c.id} to={`/containers/${c.id}`} className="container-card">
                <div className="container-card-icon">
                  <div className="grid-preview" style={{
                    gridTemplateColumns: `repeat(${Math.min(c.width || 4, 6)}, 1fr)`,
                  }}>
                    {Array.from({ length: Math.min((c.width || 4) * (c.height || 4), 36) }).map((_, i) => (
                      <div key={i} className="grid-preview-cell" />
                    ))}
                  </div>
                </div>
                <div className="container-card-info">
                  <h4>{c.name}</h4>
                  <span className="text-muted">
                    {c.width}×{c.height} grid ({(c.width || 0) * (c.height || 0)} squares)
                  </span>
                  {c.location_description && (
                    <span className="container-location">📍 {c.location_description}</span>
                  )}
                  {c.irrigation_type && (
                    <span className="container-irrigation">💧 {c.irrigation_type}</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Towers */}
      {towers.length > 0 && (
        <div className="detail-section">
          <h3>🗼 Towers</h3>
          <div className="container-list">
            {towers.map((c) => (
              <Link key={c.id} to={`/containers/${c.id}`} className="container-card">
                <div className="container-card-icon">
                  <div className="tower-preview">
                    {Array.from({ length: Math.min(c.levels || 3, 6) }).map((_, i) => (
                      <div key={i} className="tower-preview-level">
                        {Array.from({ length: Math.min(c.pockets_per_level || 4, 6) }).map((_, j) => (
                          <div key={j} className="tower-preview-pocket" />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="container-card-info">
                  <h4>{c.name}</h4>
                  <span className="text-muted">
                    {c.levels} levels × {c.pockets_per_level} pockets ({(c.levels || 0) * (c.pockets_per_level || 0)} total)
                  </span>
                  {c.location_description && (
                    <span className="container-location">📍 {c.location_description}</span>
                  )}
                  {c.irrigation_type && (
                    <span className="container-irrigation">💧 {c.irrigation_type}</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {containers.length === 0 && !error && (
        <div className="empty-state">
          <span className="empty-icon">🏡</span>
          <h3>No containers yet</h3>
          <p>Add your first garden bed or tower to get started.</p>
          <Link to="/containers/new" className="btn btn-primary">
            + Add Container
          </Link>
        </div>
      )}
    </div>
  )
}
