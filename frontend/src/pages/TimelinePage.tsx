import { apiFetch } from "../lib/api"
import { useEffect, useState, useCallback } from 'react'
import { GanttChart, TimelinePlanting } from '../components/GanttChart'

interface ContainerOption {
  id: number
  name: string
  type: string
  width: number | null
  height: number | null
  levels: number | null
  pockets_per_level: number | null
}

export function TimelinePage() {
  const [plantings, setPlantings] = useState<TimelinePlanting[]>([])
  const [containers, setContainers] = useState<ContainerOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // View controls
  const [scope, setScope] = useState<'3month' | 'year'>('3month')
  const [containerId, setContainerId] = useState<number | null>(null)
  const [groupBy, setGroupBy] = useState<'square' | 'container' | 'none'>('square')

  // Compute date range based on scope
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]

  function getDateRange(): { start: string; end: string } {
    const start = new Date(today)
    const end = new Date(today)

    if (scope === '3month') {
      start.setMonth(start.getMonth() - 1)
      end.setMonth(end.getMonth() + 2)
    } else {
      start.setMonth(0, 1) // Jan 1
      end.setMonth(11, 31) // Dec 31
    }

    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    }
  }

  const { start: startDate, end: endDate } = getDateRange()

  const fetchContainers = useCallback(async () => {
    try {
      const res = await apiFetch('/api/containers', { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        setContainers(data.map((c: ContainerOption) => ({
          id: c.id,
          name: c.name,
          type: c.type,
          width: c.width ?? null,
          height: c.height ?? null,
          levels: c.levels ?? null,
          pockets_per_level: c.pockets_per_level ?? null,
        })))
      }
    } catch {
      // ignore
    }
  }, [])

  const fetchTimeline = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      let url = `/api/plantings/timeline?start_date=${startDate}&end_date=${endDate}`
      if (containerId !== null) {
        url += `&container_id=${containerId}`
      }
      const res = await apiFetch(url, { credentials: 'include' })
      if (!res.ok) throw new Error('Failed to load timeline')
      const data = await res.json()
      setPlantings(data.plantings)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error loading timeline')
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, containerId])

  useEffect(() => {
    fetchContainers()
  }, [fetchContainers])

  useEffect(() => {
    fetchTimeline()
  }, [fetchTimeline])

  // When switching containers, reset groupBy to sensible default
  function handleContainerChange(id: number | null) {
    setContainerId(id)
    if (id === null) {
      // All containers — use container grouping, but preserve square/planting choice
      setGroupBy(prev => prev === 'none' ? 'container' : prev)
    } else {
      // Single container — square view is the main new feature
      setGroupBy(prev => prev === 'container' ? 'square' : prev)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>🗓️ Timeline</h2>
      </div>

      {/* Controls */}
      <div className="timeline-controls">
        <div className="timeline-scope-toggle">
          <button
            className={`scope-btn ${scope === '3month' ? 'active' : ''}`}
            onClick={() => setScope('3month')}
          >
            3 Months
          </button>
          <button
            className={`scope-btn ${scope === 'year' ? 'active' : ''}`}
            onClick={() => setScope('year')}
          >
            Full Year
          </button>
        </div>

        <div className="timeline-filter">
          <select
            value={containerId ?? ''}
            onChange={(e) => handleContainerChange(e.target.value ? Number(e.target.value) : null)}
            className="form-select"
          >
            <option value="">All Containers</option>
            {containers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Group by toggle */}
        <div className="timeline-scope-toggle">
          <button
            className={`scope-btn ${groupBy === 'square' ? 'active' : ''}`}
            onClick={() => setGroupBy('square')}
          >
            By Square
          </button>
          <button
            className={`scope-btn ${groupBy !== 'square' ? 'active' : ''}`}
            onClick={() => setGroupBy(containerId === null ? 'container' : 'none')}
          >
            By Planting
          </button>
        </div>

        <div className="timeline-date-info">
          <span className="text-muted">
            {startDate} — {endDate}
          </span>
          {todayStr && (
            <span className="timeline-today-badge">Today: {todayStr}</span>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-screen">
          <span className="tendril-icon">🌱</span>
          <p>Loading timeline...</p>
        </div>
      ) : (
        <GanttChart
          plantings={plantings}
          containers={containers}
          startDate={startDate}
          endDate={endDate}
          groupBy={groupBy}
        />
      )}
    </div>
  )
}
