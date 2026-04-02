import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface PlantingSeason {
  id: number
  category_id: number
  usda_zone: string
  start_month: number
  start_day: number
  end_month: number
  end_day: number
}

interface CompanionRule {
  id: number
  category_id: number
  companion_category_id: number
  companion_category_name: string | null
  companion_category_color: string | null
  relationship_type: string
}

interface CategoryDetail {
  id: number
  name: string
  color: string
  harvest_type: string
  icon_svg: string | null
  planting_seasons: PlantingSeason[]
  companion_rules: CompanionRule[]
}

interface Variety {
  id: number
  name: string
  category_id: number
  category_name: string | null
  category_color: string | null
  days_to_harvest_min: number | null
  days_to_harvest_max: number | null
  spacing: string
  sunlight: string | null
  is_climbing: boolean
  planting_method: string
}

const MONTH_NAMES = [
  '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

function formatDate(month: number, day: number): string {
  return `${MONTH_NAMES[month]} ${day}`
}

export function CategoryDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [category, setCategory] = useState<CategoryDetail | null>(null)
  const [varieties, setVarieties] = useState<Variety[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (id) {
      fetchData()
    }
  }, [id])

  async function fetchData() {
    try {
      const [catRes, varRes] = await Promise.all([
        fetch(`/api/categories/${id}`),
        fetch(`/api/varieties?category_id=${id}`),
      ])

      if (!catRes.ok) throw new Error('Category not found')
      const catData = await catRes.json()
      setCategory(catData)

      if (varRes.ok) {
        const varData = await varRes.json()
        setVarieties(varData)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load category')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading category...</p>
      </div>
    )
  }

  if (error || !category) {
    return (
      <div className="catalog-page">
        <div className="form-message error">{error || 'Category not found'}</div>
        <Link to="/catalog" className="btn btn-outline-dark">← Back to Catalog</Link>
      </div>
    )
  }

  const compatible = category.companion_rules.filter(r => r.relationship_type === 'compatible')
  const incompatible = category.companion_rules.filter(r => r.relationship_type === 'incompatible')

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to="/catalog" className="back-link">← Back to Catalog</Link>
        <div className="page-header-row">
          <div className="category-title-row">
            <div
              className="category-color-dot-lg"
              style={{ backgroundColor: category.color }}
            />
            <div>
              <h2>{category.name}</h2>
              <span className="text-muted">{category.harvest_type} harvest</span>
            </div>
          </div>
          <div className="page-header-actions">
            <Link to={`/catalog/categories/${id}/edit`} className="btn btn-outline-dark btn-sm">
              Edit Category
            </Link>
            <Link to={`/catalog/varieties/new?category=${id}`} className="btn btn-primary btn-sm">
              + Add Variety
            </Link>
          </div>
        </div>
      </div>

      {/* Planting Seasons */}
      {category.planting_seasons.length > 0 && (
        <div className="detail-section">
          <h3>Planting Seasons</h3>
          <div className="season-list">
            {category.planting_seasons.map((ps) => (
              <div key={ps.id} className="season-item">
                <span className="season-zone">Zone {ps.usda_zone}</span>
                <span className="season-dates">
                  {formatDate(ps.start_month, ps.start_day)} — {formatDate(ps.end_month, ps.end_day)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Companion Planting */}
      {(compatible.length > 0 || incompatible.length > 0) && (
        <div className="detail-section">
          <h3>Companion Planting</h3>
          {compatible.length > 0 && (
            <div className="companion-group">
              <h4 className="companion-label good">✓ Good Companions</h4>
              <div className="companion-tags">
                {compatible.map((r) => (
                  <Link
                    key={r.id}
                    to={`/catalog/categories/${r.companion_category_id}`}
                    className="companion-tag good"
                    style={{
                      borderColor: r.companion_category_color || '#ccc',
                      color: r.companion_category_color || '#333',
                    }}
                  >
                    {r.companion_category_name}
                  </Link>
                ))}
              </div>
            </div>
          )}
          {incompatible.length > 0 && (
            <div className="companion-group">
              <h4 className="companion-label bad">✗ Avoid Planting With</h4>
              <div className="companion-tags">
                {incompatible.map((r) => (
                  <Link
                    key={r.id}
                    to={`/catalog/categories/${r.companion_category_id}`}
                    className="companion-tag bad"
                  >
                    {r.companion_category_name}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Varieties */}
      <div className="detail-section">
        <div className="section-header-row">
          <h3>Varieties ({varieties.length})</h3>
          <Link to={`/catalog/varieties/new?category=${id}`} className="btn btn-primary btn-sm">
            + Add Variety
          </Link>
        </div>

        {varieties.length > 0 ? (
          <div className="variety-list">
            {varieties.map((v) => (
              <div
                key={v.id}
                className="variety-card"
                onClick={() => navigate(`/catalog/varieties/${v.id}`)}
              >
                <div className="variety-card-header">
                  <h4>{v.name}</h4>
                  {v.is_climbing && <span className="variety-badge climbing">🧗 Climbing</span>}
                </div>
                <div className="variety-card-meta">
                  {v.days_to_harvest_min && (
                    <span>
                      🕐 {v.days_to_harvest_min}
                      {v.days_to_harvest_max ? `–${v.days_to_harvest_max}` : ''} days
                    </span>
                  )}
                  <span>📐 {v.spacing}</span>
                  {v.sunlight && <span>☀️ {v.sunlight.replace('_', ' ')}</span>}
                  <span>🌱 {v.planting_method.replace('_', ' ')}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state-sm">
            <p>No varieties yet. Add your first variety for {category.name}.</p>
          </div>
        )}
      </div>
    </div>
  )
}
