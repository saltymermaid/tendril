import { apiFetch } from '../lib/api'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface ForecastPlanting {
  planting_id: number
  container_name: string | null
  square_x: number
  square_y: number
  tower_level: number | null
  status: string
  count: number | null
  harvest_date?: string
  harvest_start?: string
  harvest_end?: string
}

interface ForecastItem {
  label: string
  variety_id: number
  variety_name: string
  category_color: string
  harvest_type: 'single' | 'continuous'
  count: number | null
  starting: boolean
  ending: boolean
  overdue: boolean
  plantings: ForecastPlanting[]
}

interface ForecastWeek {
  week_start: string
  week_end: string
  items: ForecastItem[]
}

const WEEK_OPTIONS = [4, 8, 12]

function parseDate(iso: string) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function formatShort(iso: string) {
  return parseDate(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function weekTitle(index: number, week: ForecastWeek) {
  if (index === 0) return 'This week'
  if (index === 1) return 'Next week'
  return `Week of ${formatShort(week.week_start)}`
}

function locationText(plantings: ForecastPlanting[]) {
  const names = [...new Set(plantings.map((p) => p.container_name).filter(Boolean))]
  return names.join(', ')
}

export function HarvestPage() {
  const [weeks, setWeeks] = useState(8)
  const [data, setData] = useState<ForecastWeek[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch(`/api/harvest-forecast?weeks=${weeks}`, { credentials: 'include' })
        if (!res.ok) throw new Error('Failed to load harvest forecast')
        const body = await res.json()
        if (!cancelled) setData(body.weeks)
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Error loading harvest forecast')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [weeks])

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>🧺 Harvest Forecast</h2>
          <p className="page-subtitle">What's expected to come out of the garden, week by week.</p>
        </div>
      </div>

      <div className="task-filters">
        {WEEK_OPTIONS.map((n) => (
          <button
            key={n}
            className={`task-filter-btn ${weeks === n ? 'active' : ''}`}
            onClick={() => setWeeks(n)}
          >
            {n} weeks
          </button>
        ))}
      </div>

      {error && <div className="form-error">{error}</div>}

      {loading ? (
        <p className="loading-text">Loading forecast…</p>
      ) : (
        <div className="harvest-weeks">
          {data.map((week, i) => (
            <section key={week.week_start} className="harvest-week">
              <h3 className="task-group-label">
                {weekTitle(i, week)}
                <span className="text-muted harvest-week-range">
                  {formatShort(week.week_start)} – {formatShort(week.week_end)}
                </span>
              </h3>
              {week.items.length === 0 ? (
                <p className="text-muted harvest-empty">Nothing expected.</p>
              ) : (
                <ul className="harvest-list">
                  {week.items.map((item) => (
                    <li
                      key={`${item.variety_id}-${item.harvest_type}`}
                      className={`harvest-item harvest-${item.harvest_type}`}
                    >
                      <span className="harvest-dot" style={{ background: item.category_color }} />
                      <div className="harvest-item-main">
                        <Link to={`/catalog/varieties/${item.variety_id}`} className="harvest-label">
                          {item.label}
                        </Link>
                        <span className="harvest-meta text-muted">
                          {item.harvest_type === 'single' && item.plantings[0]?.harvest_date && (
                            <>{item.overdue ? 'Planned ' : ''}{formatShort(item.plantings[0].harvest_date)} · </>
                          )}
                          {locationText(item.plantings)}
                        </span>
                      </div>
                      {item.overdue && <span className="harvest-badge harvest-badge-overdue">Overdue</span>}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
