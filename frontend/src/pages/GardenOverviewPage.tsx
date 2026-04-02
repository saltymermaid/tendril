import { apiFetch } from "../lib/api"
import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'

interface OverviewPlanting {
  id: number
  square_x: number
  square_y: number
  square_width: number
  square_height: number
  tower_level: number | null
  status: string
  variety_name: string | null
  category_name: string | null
  category_color: string | null
}

interface OverviewContainer {
  id: number
  name: string
  type: string
  location_description: string | null
  width: number | null
  height: number | null
  levels: number | null
  pockets_per_level: number | null
  total_slots: number
  planted_slots: number
  plantings: OverviewPlanting[]
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

export function GardenOverviewPage() {
  const [containers, setContainers] = useState<OverviewContainer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  )
  const todayStr = new Date().toISOString().split('T')[0]

  const fetchOverview = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/containers/overview?date=${selectedDate}`)
      if (!res.ok) throw new Error('Failed to load overview')
      setContainers(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load overview')
    } finally {
      setLoading(false)
    }
  }, [selectedDate])

  useEffect(() => {
    fetchOverview()
  }, [fetchOverview])

  function changeDate(days: number) {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + days)
    setSelectedDate(d.toISOString().split('T')[0])
  }

  function goToToday() {
    setSelectedDate(new Date().toISOString().split('T')[0])
  }

  function getPlantingAt(container: OverviewContainer, x: number, y: number): OverviewPlanting | undefined {
    return container.plantings.find(p => {
      const inX = x >= p.square_x && x < p.square_x + p.square_width
      const inY = y >= p.square_y && y < p.square_y + p.square_height
      return inX && inY
    })
  }

  function getPlantingAtLevel(container: OverviewContainer, level: number, pocket: number): OverviewPlanting | undefined {
    return container.plantings.find(p => p.tower_level === level && p.square_x === pocket)
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading garden overview...</p>
      </div>
    )
  }

  return (
    <div className="catalog-page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2>🏡 Garden Overview</h2>
            <p className="text-muted">All your containers at a glance</p>
          </div>
          <Link to="/containers/new" className="btn btn-primary">
            + Add Container
          </Link>
        </div>
      </div>

      {/* Time Slider */}
      <div className="time-slider">
        <button className="time-slider-btn" onClick={() => changeDate(-7)} title="Back 1 week">⏪</button>
        <button className="time-slider-btn" onClick={() => changeDate(-1)} title="Previous day">◀</button>
        <input
          type="date"
          className="time-slider-date"
          value={selectedDate}
          onChange={e => setSelectedDate(e.target.value)}
        />
        <button className="time-slider-btn" onClick={() => changeDate(1)} title="Next day">▶</button>
        <button className="time-slider-btn" onClick={() => changeDate(7)} title="Forward 1 week">⏩</button>
        {selectedDate !== todayStr && (
          <button className="time-slider-today" onClick={goToToday}>Today</button>
        )}
      </div>
      {selectedDate !== todayStr && (
        <div className={`time-slider-label ${selectedDate < todayStr ? 'past' : 'future'}`}>
          {selectedDate < todayStr ? '📜 Viewing historical state' : '🔮 Viewing planned future'}
        </div>
      )}

      {error && <div className="form-message error">{error}</div>}

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

      {/* Overview Grid */}
      <div className="overview-grid">
        {containers.map(c => (
          <Link key={c.id} to={`/containers/${c.id}`} className="overview-card">
            <div className="overview-card-header">
              <h3>{c.name}</h3>
              <span className="overview-stats">
                {c.planted_slots}/{c.total_slots} planted
              </span>
            </div>

            {c.location_description && (
              <span className="overview-location">📍 {c.location_description}</span>
            )}

            {/* Mini Grid Bed */}
            {c.type === 'grid_bed' && (
              <div className="mini-grid" style={{
                gridTemplateColumns: `repeat(${c.width || 1}, 1fr)`,
              }}>
                {Array.from({ length: (c.height || 0) }).map((_, y) =>
                  Array.from({ length: (c.width || 0) }).map((_, x) => {
                    const planting = getPlantingAt(c, x, y)
                    return (
                      <div
                        key={`${x}-${y}`}
                        className={`mini-square ${planting ? 'planted' : 'empty'} ${planting?.status || ''}`}
                        style={planting ? {
                          backgroundColor: (planting.category_color || '#86efac') + '60',
                          borderColor: planting.category_color || undefined,
                        } : undefined}
                        title={planting
                          ? `${ROW_LABELS[y]}${x + 1}: ${planting.variety_name}`
                          : `${ROW_LABELS[y]}${x + 1}: empty`
                        }
                      />
                    )
                  })
                )}
              </div>
            )}

            {/* Mini Tower */}
            {c.type === 'tower' && (
              <div className="mini-tower">
                {Array.from({ length: (c.levels || 0) }).map((_, level) => (
                  <div key={level} className="mini-tower-level">
                    {Array.from({ length: (c.pockets_per_level || 0) }).map((_, pocket) => {
                      const planting = getPlantingAtLevel(c, level, pocket)
                      return (
                        <div
                          key={pocket}
                          className={`mini-pocket ${planting ? 'planted' : 'empty'}`}
                          style={planting ? {
                            backgroundColor: (planting.category_color || '#86efac') + '60',
                            borderColor: planting.category_color || undefined,
                          } : undefined}
                          title={planting
                            ? `L${level + 1}P${pocket + 1}: ${planting.variety_name}`
                            : `L${level + 1}P${pocket + 1}: empty`
                          }
                        />
                      )
                    })}
                  </div>
                ))}
              </div>
            )}

            {/* Planting Legend */}
            {c.plantings.length > 0 && (
              <div className="overview-legend">
                {Array.from(new Set(c.plantings.map(p => p.category_name))).map(cat => {
                  const sample = c.plantings.find(p => p.category_name === cat)
                  return (
                    <span key={cat} className="overview-legend-item">
                      <span
                        className="overview-legend-dot"
                        style={{ backgroundColor: sample?.category_color || '#ccc' }}
                      />
                      {cat}
                    </span>
                  )
                })}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}
