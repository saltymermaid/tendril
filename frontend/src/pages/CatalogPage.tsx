import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

interface Category {
  id: number
  name: string
  color: string
  harvest_type: string
  icon_svg: string | null
  variety_count: number
}

export function CatalogPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchCategories()
  }, [])

  async function fetchCategories() {
    try {
      const res = await fetch('/api/categories')
      if (!res.ok) throw new Error('Failed to load categories')
      const data = await res.json()
      setCategories(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load categories')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading catalog...</p>
      </div>
    )
  }

  return (
    <div className="catalog-page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2>Seed Catalog</h2>
            <p className="text-muted">Browse plant categories and manage your varieties</p>
          </div>
          <Link to="/catalog/categories/new" className="btn btn-primary">
            + Add Category
          </Link>
        </div>
      </div>

      {error && <div className="form-message error">{error}</div>}

      <div className="category-grid">
        {categories.map((cat) => (
          <Link
            key={cat.id}
            to={`/catalog/categories/${cat.id}`}
            className="category-card"
            style={{ borderTopColor: cat.color }}
          >
            <div className="category-card-icon" style={{ color: cat.color }}>
              {cat.icon_svg ? (
                <span dangerouslySetInnerHTML={{ __html: cat.icon_svg }} />
              ) : (
                <span className="category-emoji">🌱</span>
              )}
            </div>
            <div className="category-card-info">
              <h3>{cat.name}</h3>
              <span className="category-card-meta">
                {cat.variety_count} {cat.variety_count === 1 ? 'variety' : 'varieties'}
              </span>
              <span
                className="category-card-badge"
                style={{ backgroundColor: cat.color + '20', color: cat.color }}
              >
                {cat.harvest_type}
              </span>
            </div>
          </Link>
        ))}
      </div>

      {categories.length === 0 && !error && (
        <div className="empty-state">
          <span className="empty-icon">📦</span>
          <h3>No categories yet</h3>
          <p>Create your first plant category to get started.</p>
          <Link to="/catalog/categories/new" className="btn btn-primary">
            + Add Category
          </Link>
        </div>
      )}
    </div>
  )
}
