import { apiFetch } from "../lib/api"
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface Yard {
  id: number
  name: string
  width: number
  height: number
}

export function YardsPage() {
  const [yards, setYards] = useState<Yard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchYards()
  }, [])

  async function fetchYards() {
    try {
      const res = await apiFetch('/api/yards')
      if (!res.ok) throw new Error('Failed to load yards')
      setYards(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load yards')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading yards...</p>
      </div>
    )
  }

  return (
    <div className="catalog-page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2>Yards</h2>
            <p className="text-muted">See how your beds and features are laid out in space</p>
          </div>
          <Link to="/yards/new" className="btn btn-primary">
            + Add Yard
          </Link>
        </div>
      </div>

      {error && <div className="form-message error">{error}</div>}

      {yards.length > 0 && (
        <div className="detail-section">
          <div className="container-list">
            {yards.map((y) => (
              <Link key={y.id} to={`/yards/${y.id}`} className="container-card">
                <div className="container-card-icon">
                  <div
                    className="grid-preview"
                    style={{ gridTemplateColumns: `repeat(${Math.min(y.width, 8)}, 1fr)` }}
                  >
                    {Array.from({ length: Math.min(y.width * y.height, 64) }).map((_, i) => (
                      <div key={i} className="gp-cell" />
                    ))}
                  </div>
                </div>
                <div className="container-card-info">
                  <h4>{y.name}</h4>
                  <span className="text-muted">
                    {y.width}×{y.height} squares
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {yards.length === 0 && !error && (
        <div className="empty-state">
          <span className="empty-icon">🏡</span>
          <h3>No yards yet</h3>
          <p>Lay out your North yard, backyard, or any area to see your beds and features in place.</p>
          <Link to="/yards/new" className="btn btn-primary">
            + Add Yard
          </Link>
        </div>
      )}
    </div>
  )
}
