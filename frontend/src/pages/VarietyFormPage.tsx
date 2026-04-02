import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom'

interface Category {
  id: number
  name: string
  color: string
}

interface VarietyFormData {
  name: string
  category_id: number | ''
  season_override_start_month: number | ''
  season_override_start_day: number | ''
  season_override_end_month: number | ''
  season_override_end_day: number | ''
  days_to_germination_min: number | ''
  days_to_germination_max: number | ''
  days_to_harvest_min: number | ''
  days_to_harvest_max: number | ''
  planting_depth: string
  spacing: string
  sunlight: string
  is_climbing: boolean
  planting_method: string
  seed_packet_photo_url: string
  source_url: string
  notes: string
}

const EMPTY_FORM: VarietyFormData = {
  name: '',
  category_id: '',
  season_override_start_month: '',
  season_override_start_day: '',
  season_override_end_month: '',
  season_override_end_day: '',
  days_to_germination_min: '',
  days_to_germination_max: '',
  days_to_harvest_min: '',
  days_to_harvest_max: '',
  planting_depth: '',
  spacing: '1x1',
  sunlight: 'full_sun',
  is_climbing: false,
  planting_method: 'both',
  seed_packet_photo_url: '',
  source_url: '',
  notes: '',
}

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]

/**
 * Compress an image file to JPEG with max dimension and quality settings.
 * Returns { base64, mediaType } where base64 has no data: prefix.
 */
async function compressImage(
  file: File,
  maxWidth = 1200,
  quality = 0.8,
): Promise<{ base64: string; mediaType: string }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      URL.revokeObjectURL(url)

      let { width, height } = img
      if (width > maxWidth) {
        height = Math.round((height * maxWidth) / width)
        width = maxWidth
      }

      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Could not get canvas context'))
        return
      }
      ctx.drawImage(img, 0, 0, width, height)

      const dataUrl = canvas.toDataURL('image/jpeg', quality)
      // Strip the data:image/jpeg;base64, prefix
      const base64 = dataUrl.split(',')[1]
      resolve({ base64, mediaType: 'image/jpeg' })
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to load image'))
    }

    img.src = url
  })
}

export function VarietyFormPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [form, setForm] = useState<VarietyFormData>({ ...EMPTY_FORM })
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // AI extraction state
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [extracting, setExtracting] = useState(false)
  const [extractError, setExtractError] = useState('')
  const [extractSuccess, setExtractSuccess] = useState('')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [hasApiKey, setHasApiKey] = useState(false)

  useEffect(() => {
    loadData()
  }, [id])

  async function loadData() {
    try {
      // Always load categories for the dropdown
      const catRes = await fetch('/api/categories')
      if (catRes.ok) {
        setCategories(await catRes.json())
      }

      // Check if user has Claude API key
      const settingsRes = await fetch('/api/settings', { credentials: 'include' })
      if (settingsRes.ok) {
        const settings = await settingsRes.json()
        setHasApiKey(settings.has_claude_api_key)
      }

      if (isEdit && id) {
        const res = await fetch(`/api/varieties/${id}`)
        if (!res.ok) throw new Error('Variety not found')
        const data = await res.json()
        setForm({
          name: data.name,
          category_id: data.category_id,
          season_override_start_month: data.season_override_start_month ?? '',
          season_override_start_day: data.season_override_start_day ?? '',
          season_override_end_month: data.season_override_end_month ?? '',
          season_override_end_day: data.season_override_end_day ?? '',
          days_to_germination_min: data.days_to_germination_min ?? '',
          days_to_germination_max: data.days_to_germination_max ?? '',
          days_to_harvest_min: data.days_to_harvest_min ?? '',
          days_to_harvest_max: data.days_to_harvest_max ?? '',
          planting_depth: data.planting_depth || '',
          spacing: data.spacing,
          sunlight: data.sunlight || 'full_sun',
          is_climbing: data.is_climbing,
          planting_method: data.planting_method,
          seed_packet_photo_url: data.seed_packet_photo_url || '',
          source_url: data.source_url || '',
          notes: data.notes || '',
        })
        if (data.seed_packet_photo_url) {
          setPreviewUrl(data.seed_packet_photo_url)
        }
      } else {
        // Pre-select category from URL param
        const catParam = searchParams.get('category')
        if (catParam) {
          setForm((prev) => ({ ...prev, category_id: parseInt(catParam) }))
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  async function handlePhotoCapture(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setExtractError('')
    setExtractSuccess('')

    // Show preview immediately
    const objectUrl = URL.createObjectURL(file)
    setPreviewUrl(objectUrl)

    // Compress the image
    setExtracting(true)
    try {
      const { base64, mediaType } = await compressImage(file)

      // Send to AI extraction endpoint
      const res = await fetch('/api/varieties/extract-from-photo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ image_base64: base64, media_type: mediaType }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Extraction failed' }))
        throw new Error(err.detail || 'Extraction failed')
      }

      const result = await res.json()

      if (result.success && result.data) {
        // Auto-populate form fields with extracted data
        const d = result.data
        setForm((prev) => ({
          ...prev,
          name: d.name || prev.name,
          days_to_germination_min: d.days_to_germination_min ?? prev.days_to_germination_min,
          days_to_germination_max: d.days_to_germination_max ?? prev.days_to_germination_max,
          days_to_harvest_min: d.days_to_harvest_min ?? prev.days_to_harvest_min,
          days_to_harvest_max: d.days_to_harvest_max ?? prev.days_to_harvest_max,
          planting_depth: d.planting_depth || prev.planting_depth,
          spacing: d.spacing || prev.spacing,
          sunlight: d.sunlight || prev.sunlight,
          is_climbing: d.is_climbing ?? prev.is_climbing,
          planting_method: d.planting_method || prev.planting_method,
          notes: d.notes ? (prev.notes ? prev.notes + '\n\n' + d.notes : d.notes) : prev.notes,
        }))

        const fieldCount = Object.values(d).filter((v) => v !== null && v !== undefined).length
        setExtractSuccess(`Extracted ${fieldCount} fields from seed packet. Review and adjust as needed.`)
        setTimeout(() => setExtractSuccess(''), 5000)
      } else {
        setExtractError(result.error || 'Could not extract data from photo.')
      }
    } catch (err: unknown) {
      setExtractError(err instanceof Error ? err.message : 'Photo extraction failed')
    } finally {
      setExtracting(false)
      // Reset file input so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const body: Record<string, unknown> = {
        name: form.name,
        category_id: form.category_id,
        spacing: form.spacing,
        sunlight: form.sunlight || null,
        is_climbing: form.is_climbing,
        planting_method: form.planting_method,
        planting_depth: form.planting_depth || null,
        seed_packet_photo_url: form.seed_packet_photo_url || null,
        source_url: form.source_url || null,
        notes: form.notes || null,
        season_override_start_month: form.season_override_start_month || null,
        season_override_start_day: form.season_override_start_day || null,
        season_override_end_month: form.season_override_end_month || null,
        season_override_end_day: form.season_override_end_day || null,
        days_to_germination_min: form.days_to_germination_min || null,
        days_to_germination_max: form.days_to_germination_max || null,
        days_to_harvest_min: form.days_to_harvest_min || null,
        days_to_harvest_max: form.days_to_harvest_max || null,
      }

      const url = isEdit ? `/api/varieties/${id}` : '/api/varieties'
      const method = isEdit ? 'PUT' : 'POST'

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save variety')
      }

      const saved = await res.json()
      navigate(`/catalog/varieties/${saved.id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save variety')
    } finally {
      setSaving(false)
    }
  }

  function updateField(field: keyof VarietyFormData, value: string | number | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="tendril-icon">🌱</span>
        <p>Loading...</p>
      </div>
    )
  }

  const backUrl = isEdit
    ? `/catalog/varieties/${id}`
    : form.category_id
      ? `/catalog/categories/${form.category_id}`
      : '/catalog'

  return (
    <div className="catalog-page">
      <div className="page-header">
        <Link to={backUrl} className="back-link">← Back</Link>
        <h2>{isEdit ? 'Edit Variety' : 'New Variety'}</h2>
      </div>

      {error && <div className="form-message error">{error}</div>}

      {/* Seed Packet Photo Import */}
      <div className="form-card photo-import-card">
        <h3>📸 Seed Packet Photo Import</h3>
        <p className="form-help" style={{ marginBottom: 'var(--space-3)' }}>
          Take a photo of a seed packet to auto-fill growing data using AI.
        </p>

        {!hasApiKey && (
          <div className="form-message" style={{ marginBottom: 'var(--space-3)', background: 'var(--warning-bg, #fff3cd)', color: 'var(--warning-text, #856404)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
            ⚠️ No Claude API key configured.{' '}
            <Link to="/settings" style={{ color: 'inherit', fontWeight: 600 }}>Add one in Settings</Link>{' '}
            to enable AI extraction.
          </div>
        )}

        <div className="photo-import-controls">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handlePhotoCapture}
            style={{ display: 'none' }}
            id="seed-packet-photo"
          />

          <div className="photo-import-buttons">
            <button
              type="button"
              className="btn btn-outline-dark"
              onClick={() => fileInputRef.current?.click()}
              disabled={extracting || !hasApiKey}
            >
              {extracting ? '🔄 Analyzing...' : '📷 Capture Seed Packet'}
            </button>

            <button
              type="button"
              className="btn btn-outline-dark"
              onClick={() => {
                // Remove capture attribute for gallery selection
                if (fileInputRef.current) {
                  fileInputRef.current.removeAttribute('capture')
                  fileInputRef.current.click()
                  // Restore capture attribute after
                  setTimeout(() => {
                    if (fileInputRef.current) {
                      fileInputRef.current.setAttribute('capture', 'environment')
                    }
                  }, 100)
                }
              }}
              disabled={extracting || !hasApiKey}
            >
              🖼️ Choose from Gallery
            </button>
          </div>

          {extracting && (
            <div className="extract-loading">
              <div className="extract-spinner"></div>
              <span>Analyzing seed packet with AI...</span>
            </div>
          )}

          {extractError && (
            <div className="form-message error" style={{ marginTop: 'var(--space-3)' }}>
              {extractError}
            </div>
          )}

          {extractSuccess && (
            <div className="form-message success" style={{ marginTop: 'var(--space-3)' }}>
              ✅ {extractSuccess}
            </div>
          )}

          {previewUrl && (
            <div className="photo-preview" style={{ marginTop: 'var(--space-3)' }}>
              <img
                src={previewUrl}
                alt="Seed packet"
                style={{
                  maxWidth: '200px',
                  maxHeight: '200px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  objectFit: 'cover',
                }}
              />
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="detail-form">
        {/* Basic Info */}
        <div className="form-card">
          <h3>Basic Information</h3>
          <div className="form-group">
            <label className="form-label">Name *</label>
            <input
              type="text"
              className="input"
              value={form.name}
              onChange={(e) => updateField('name', e.target.value)}
              required
              placeholder="e.g., Cherokee Purple"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category *</label>
            <select
              className="input"
              value={form.category_id}
              onChange={(e) => updateField('category_id', parseInt(e.target.value))}
              required
            >
              <option value="">Select a category...</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Growth Data */}
        <div className="form-card">
          <h3>Growth Data</h3>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Days to Germination (min)</label>
              <input
                type="number"
                className="input"
                value={form.days_to_germination_min}
                onChange={(e) => updateField('days_to_germination_min', e.target.value ? parseInt(e.target.value) : '')}
                min={0}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Days to Germination (max)</label>
              <input
                type="number"
                className="input"
                value={form.days_to_germination_max}
                onChange={(e) => updateField('days_to_germination_max', e.target.value ? parseInt(e.target.value) : '')}
                min={0}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Days to Harvest (min)</label>
              <input
                type="number"
                className="input"
                value={form.days_to_harvest_min}
                onChange={(e) => updateField('days_to_harvest_min', e.target.value ? parseInt(e.target.value) : '')}
                min={0}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Days to Harvest (max)</label>
              <input
                type="number"
                className="input"
                value={form.days_to_harvest_max}
                onChange={(e) => updateField('days_to_harvest_max', e.target.value ? parseInt(e.target.value) : '')}
                min={0}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Planting Depth</label>
              <input
                type="text"
                className="input"
                value={form.planting_depth}
                onChange={(e) => updateField('planting_depth', e.target.value)}
                placeholder='e.g., 1/4"'
              />
            </div>
            <div className="form-group">
              <label className="form-label">Spacing</label>
              <select
                className="input"
                value={form.spacing}
                onChange={(e) => updateField('spacing', e.target.value)}
              >
                <option value="1x1">1×1 (1 square)</option>
                <option value="1x2">1×2 (2 squares)</option>
                <option value="2x2">2×2 (4 squares)</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Sunlight</label>
              <select
                className="input"
                value={form.sunlight}
                onChange={(e) => updateField('sunlight', e.target.value)}
              >
                <option value="full_sun">Full Sun</option>
                <option value="partial_shade">Partial Shade</option>
                <option value="full_shade">Full Shade</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Planting Method</label>
              <select
                className="input"
                value={form.planting_method}
                onChange={(e) => updateField('planting_method', e.target.value)}
              >
                <option value="both">Both</option>
                <option value="direct_sow">Direct Sow</option>
                <option value="transplant">Transplant</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              <input
                type="checkbox"
                checked={form.is_climbing}
                onChange={(e) => updateField('is_climbing', e.target.checked)}
                style={{ marginRight: 'var(--space-2)' }}
              />
              Climbing plant (requires trellis/support)
            </label>
          </div>
        </div>

        {/* Season Override */}
        <div className="form-card">
          <h3>Season Override (optional)</h3>
          <p className="form-help" style={{ marginBottom: 'var(--space-4)' }}>
            Override the category's planting season for this specific variety.
          </p>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Start Month</label>
              <select
                className="input"
                value={form.season_override_start_month}
                onChange={(e) => updateField('season_override_start_month', e.target.value ? parseInt(e.target.value) : '')}
              >
                <option value="">—</option>
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Start Day</label>
              <input
                type="number"
                className="input"
                value={form.season_override_start_day}
                onChange={(e) => updateField('season_override_start_day', e.target.value ? parseInt(e.target.value) : '')}
                min={1}
                max={31}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">End Month</label>
              <select
                className="input"
                value={form.season_override_end_month}
                onChange={(e) => updateField('season_override_end_month', e.target.value ? parseInt(e.target.value) : '')}
              >
                <option value="">—</option>
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">End Day</label>
              <input
                type="number"
                className="input"
                value={form.season_override_end_day}
                onChange={(e) => updateField('season_override_end_day', e.target.value ? parseInt(e.target.value) : '')}
                min={1}
                max={31}
              />
            </div>
          </div>
        </div>

        {/* Notes & Links */}
        <div className="form-card">
          <h3>Notes & Links</h3>
          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea
              className="input textarea"
              value={form.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              rows={4}
              placeholder="Growing tips, observations, etc."
            />
          </div>
          <div className="form-group">
            <label className="form-label">Source / Purchase URL</label>
            <input
              type="url"
              className="input"
              value={form.source_url}
              onChange={(e) => updateField('source_url', e.target.value)}
              placeholder="https://..."
            />
          </div>
          <div className="form-group">
            <label className="form-label">Seed Packet Photo URL</label>
            <input
              type="url"
              className="input"
              value={form.seed_packet_photo_url}
              onChange={(e) => updateField('seed_packet_photo_url', e.target.value)}
              placeholder="https://..."
            />
            <p className="form-help">Direct URL to a seed packet image (optional).</p>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : isEdit ? 'Update Variety' : 'Create Variety'}
          </button>
          <Link to={backUrl} className="btn btn-outline-dark">Cancel</Link>
        </div>
      </form>
    </div>
  )
}
