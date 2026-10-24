import { apiFetch } from "../lib/api"
import { activatePlanting, type StillGrowing } from '../lib/plantings'
import { StillGrowingModal } from '../components/StillGrowingModal'
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
  yard_id: number | null
}

type ContainerSummary = Pick<
  ContainerDetail,
  'id' | 'name' | 'type' | 'width' | 'height' | 'levels' | 'pockets_per_level'
>

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
  seed_start_date: string | null
  status: string
  planting_method: string | null
  quantity: number | null
  variety_name: string | null
  category_name: string | null
  category_color: string | null
  category_icon_svg: string | null
  // Still growing past its estimated end_date — it keeps its squares until marked done
  overdue: boolean
  // The planned planting waiting for this overdue planting's squares
  next_planting: { id: number; variety_name: string | null; start_date: string } | null
}

interface Variety {
  id: number
  name: string
  category_id: number
  category_name: string | null
  category_color: string | null
  days_to_harvest_max: number | null
}

interface PlantStart {
  id: number
  variety_id: number
  variety_name: string | null
  category_name: string | null
  category_color: string | null
  start_date: string
  quantity: number
}

interface Category {
  id: number
  name: string
  color: string
}

interface RecommendationVariety {
  variety_id: number
  variety_name: string
  score: number
  days_to_harvest_min: number | null
  days_to_harvest_max: number | null
  planting_method: string
  is_climbing: boolean
  spacing: string
  warnings: string[]
  boosts: string[]
}

interface RecommendationCategory {
  category_id: number
  category_name: string
  category_color: string
  varieties: RecommendationVariety[]
}

interface RecommendationData {
  date: string
  container_id: number
  square_x: number
  square_y: number
  tower_level: number | null
  total_varieties: number
  categories: RecommendationCategory[]
}

const SUPPORT_ICONS: Record<string, string> = {
  trellis: '🪜',
  cage: '🔲',
  pole: '🪵',
}

const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

function statusLabel(status: string): string {
  switch (status) {
    case 'not_started': return 'Planned'
    case 'in_progress': return 'Growing'
    case 'complete': return 'Done'
    default: return status.replace(/_/g, ' ')
  }
}

// A planned planting "Plant Now" is about to put in the ground
type PlantingToActivate = { id: number; variety_name: string | null }

// "Up next" note for an overdue planting with something planned behind it. `due` once the
// planned start date has arrived (as of the date being viewed) — time to pull the old plant.
function nextUpInfo(p: PlantingData, asOf: string): { text: string; due: boolean } | null {
  if (!p.next_planting) return null
  const due = p.next_planting.start_date <= asOf
  const name = p.next_planting.variety_name ?? 'A planting'
  return {
    text: due
      ? `${name} is ready to go in (planned for ${p.next_planting.start_date})`
      : `Up next: ${name}, planned for ${p.next_planting.start_date}`,
    due,
  }
}

export function ContainerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [container, setContainer] = useState<ContainerDetail | null>(null)
  const [plantings, setPlantings] = useState<PlantingData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  // Time slider state
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  )
  const todayStr = new Date().toISOString().split('T')[0]

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
  const [plantStarts, setPlantStarts] = useState<PlantStart[]>([])
  const [selectedStartId, setSelectedStartId] = useState<number | null>(null)
  const [plantingForm, setPlantingForm] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    planting_method: '' as string,
    quantity: '' as string,
    square_width: 1,
    square_height: 1,
  })

  // Auto-compute end_date from days_to_harvest, which is measured from seed —
  // anchor on the plant start's seed date when transplanting one, not on
  // start_date (which is just when it goes into this square).
  useEffect(() => {
    if (!selectedVariety || !varieties.length) return
    const variety = varieties.find(v => v.id === selectedVariety)
    if (!variety?.days_to_harvest_max) return
    const selectedStart = selectedStartId ? plantStarts.find(s => s.id === selectedStartId) : null
    const anchorDateStr = selectedStart ? selectedStart.start_date : plantingForm.start_date
    // Parse the anchor date in local time to avoid UTC offset issues
    const [yr, mo, dy] = anchorDateStr.split('-').map(Number)
    const end = new Date(yr, mo - 1, dy + variety.days_to_harvest_max)
    const endDate = `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, '0')}-${String(end.getDate()).padStart(2, '0')}`
    setPlantingForm(prev => ({ ...prev, end_date: endDate }))
  }, [selectedVariety, plantingForm.start_date, selectedStartId, plantStarts])

  const [plantingError, setPlantingError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Selected planting for detail view
  const [selectedPlanting, setSelectedPlanting] = useState<PlantingData | null>(null)
  const [activating, setActivating] = useState(false)
  const [activateError, setActivateError] = useState('')
  // Set when "Plant Now" finds an earlier planting still growing on these squares
  const [stillGrowing, setStillGrowing] = useState<{
    planting: PlantingToActivate
    growing: StillGrowing[]
  } | null>(null)

  // Planting edit state
  const [editingPlanting, setEditingPlanting] = useState(false)
  const [editForm, setEditForm] = useState({
    container_id: 0,
    square_x: 0,
    square_y: 0,
    tower_level: null as number | null,
    start_date: '',
    end_date: '',
    seed_start_date: '' as string,
    planting_method: '' as string,
    quantity: '' as string,
  })
  const [allContainers, setAllContainers] = useState<ContainerSummary[]>([])
  const [editError, setEditError] = useState('')
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [deletingPlanting, setDeletingPlanting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  // Recommendation state
  const [recommendations, setRecommendations] = useState<RecommendationData | null>(null)
  const [recLoading, setRecLoading] = useState(false)
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set())
  const [recSquare, setRecSquare] = useState<{ x: number; y: number; towerLevel?: number } | null>(null)
  const [recDate, setRecDate] = useState<string>(todayStr)

  // Square action chooser (plant vs recommend)
  const [squareChooser, setSquareChooser] = useState<{ x: number; y: number; towerLevel?: number } | null>(null)

  // Start-first picker (choose a started seedling, then land in the planting form pre-filled)
  const [startPickerModal, setStartPickerModal] = useState<{ x: number; y: number; towerLevel?: number } | null>(null)
  const [startPickerCategory, setStartPickerCategory] = useState<string | null>(null)

  const fetchContainer = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/containers/${id}`)
      if (!res.ok) throw new Error('Container not found')
      setContainer(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load container')
    }
  }, [id])

  const fetchPlantings = useCallback(async (dateFilter?: string) => {
    try {
      const dateParam = dateFilter || selectedDate
      const url = dateParam
        ? `/api/plantings/by-container/${id}?as_of=${dateParam}`
        : `/api/plantings/by-container/${id}`
      const res = await apiFetch(url)
      if (!res.ok) throw new Error('Failed to load plantings')
      setPlantings(await res.json())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load plantings')
    }
  }, [id, selectedDate])

  useEffect(() => {
    if (id) {
      Promise.all([fetchContainer(), fetchPlantings()]).finally(() => setLoading(false))
    }
  }, [id, fetchContainer, fetchPlantings])

  // Refetch plantings when date changes
  useEffect(() => {
    if (id && !loading) {
      fetchPlantings()
    }
  }, [selectedDate])

  function changeDate(days: number) {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + days)
    setSelectedDate(d.toISOString().split('T')[0])
  }

  function goToToday() {
    setSelectedDate(new Date().toISOString().split('T')[0])
  }

  async function fetchVarietiesAndCategories() {
    try {
      const [varRes, catRes] = await Promise.all([
        apiFetch('/api/varieties'),
        apiFetch('/api/categories'),
      ])
      if (varRes.ok) setVarieties(await varRes.json())
      if (catRes.ok) setCategories(await catRes.json())
    } catch {
      // Non-critical
    }
  }

  async function fetchPlantStarts() {
    try {
      const res = await apiFetch('/api/plant-starts')
      if (res.ok) setPlantStarts(await res.json())
    } catch {
      // Non-critical
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this container? This cannot be undone.')) return
    setDeleting(true)
    try {
      const res = await apiFetch(`/api/containers/${id}`, { method: 'DELETE' })
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
      const res = await apiFetch(`/api/containers/${id}/squares/${x}/${y}/support`, {
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
      await apiFetch(`/api/containers/${id}/squares/${x}/${y}/support`, { method: 'DELETE' })
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
    // Backend already filters by as_of date; just match position
    return plantings.find((p: PlantingData) => {
      const inX = x >= p.square_x && x < p.square_x + p.square_width
      const inY = y >= p.square_y && y < p.square_y + p.square_height
      return inX && inY
    })
  }

  function getPlantingAtLevel(level: number, pocket: number): PlantingData | undefined {
    // Backend already filters by as_of date; just match position
    return plantings.find((p: PlantingData) => {
      return p.tower_level === level && p.square_x === pocket
    })
  }

  async function handleDeletePlanting() {
    if (!selectedPlanting) return
    const warning = selectedPlanting.status === 'not_started'
      ? 'Remove this planned planting?'
      : `Permanently delete this ${statusLabel(selectedPlanting.status).toLowerCase()} planting and all record of it? This can't be undone.`
    if (!window.confirm(warning)) return

    setDeletingPlanting(true)
    setDeleteError('')
    try {
      const res = await apiFetch(`/api/plantings/${selectedPlanting.id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to delete planting')
      }
      setSelectedPlanting(null)
      fetchPlantings(selectedDate)
      fetchPlantStarts()
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete planting')
    } finally {
      setDeletingPlanting(false)
    }
  }

  async function handleActivatePlanting(target: PlantingToActivate, replaceReason?: string) {
    setActivating(true)
    setActivateError('')
    try {
      const result = await activatePlanting<PlantingData>(target.id, replaceReason)
      if (result.ok) {
        setSelectedPlanting(null)
        setStillGrowing(null)
        fetchPlantings(selectedDate)
      } else if ('stillGrowing' in result) {
        setStillGrowing({ planting: target, growing: result.stillGrowing })
      } else {
        setActivateError(result.error)
      }
    } catch (err: unknown) {
      setActivateError(err instanceof Error ? err.message : 'Failed to mark as planted')
    } finally {
      setActivating(false)
    }
  }

  function startEditPlanting() {
    if (!selectedPlanting) return
    setEditForm({
      container_id: selectedPlanting.container_id,
      square_x: selectedPlanting.square_x,
      square_y: selectedPlanting.square_y,
      tower_level: selectedPlanting.tower_level,
      start_date: selectedPlanting.start_date,
      end_date: selectedPlanting.end_date,
      seed_start_date: selectedPlanting.seed_start_date || '',
      planting_method: selectedPlanting.planting_method || '',
      quantity: selectedPlanting.quantity ? String(selectedPlanting.quantity) : '',
    })
    setEditError('')
    setEditingPlanting(true)
    // Containers to move into — loaded lazily since only the edit form needs them
    if (!allContainers.length) {
      apiFetch('/api/containers')
        .then(res => (res.ok ? res.json() : []))
        .then(setAllContainers)
        .catch(() => {})
    }
  }

  // Changing the target container resets the position to its first square/pocket
  function setEditContainer(containerId: number) {
    const target = allContainers.find(c => c.id === containerId)
    setEditForm(prev => ({
      ...prev,
      container_id: containerId,
      square_x: 0,
      square_y: 0,
      tower_level: target?.type === 'tower' ? 0 : null,
    }))
  }

  function cancelEditPlanting() {
    setEditingPlanting(false)
    setEditError('')
  }

  async function handleUpdatePlanting(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedPlanting) return

    setEditSubmitting(true)
    setEditError('')

    try {
      const body: Record<string, unknown> = {
        container_id: editForm.container_id,
        square_x: editForm.square_x,
        square_y: editForm.square_y,
        tower_level: editForm.tower_level,
        start_date: editForm.start_date,
        end_date: editForm.end_date,
        seed_start_date: editForm.seed_start_date || null,
        planting_method: editForm.planting_method || null,
        quantity: editForm.quantity ? Number(editForm.quantity) : null,
      }

      const res = await apiFetch(`/api/plantings/${selectedPlanting.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to update planting')
      }

      const updated: PlantingData = await res.json()
      if (updated.container_id !== selectedPlanting.container_id) {
        // Moved to another container — it no longer belongs on this grid
        setSelectedPlanting(null)
        setEditingPlanting(false)
        fetchPlantings(selectedDate)
        return
      }
      setSelectedPlanting(updated)
      setPlantings(prev => prev.map(p => (p.id === updated.id ? updated : p)))
      setEditingPlanting(false)
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : 'Failed to update planting')
    } finally {
      setEditSubmitting(false)
    }
  }

  async function openPlantingModal(x: number, y: number, towerLevel?: number) {
    setPlantingModal({ x, y, towerLevel })
    setPlantingError('')
    setSelectedVariety(null)
    setSelectedStartId(null)
    setVarietySearch('')
    setSelectedCategory(null)

    // Compute smart default start_date:
    // If there are existing plantings at this square → later of (day after last end_date) or today
    // If the square is empty → today
    const todayStr = new Date().toISOString().split('T')[0]
    let defaultStartDate = todayStr
    try {
      const res = await apiFetch(`/api/plantings/by-container/${id}`)
      if (res.ok) {
        const allPlantings: PlantingData[] = await res.json()
        const squarePlantings = allPlantings.filter(p => {
          if (towerLevel !== undefined) {
            return p.tower_level === towerLevel && p.square_x === x
          }
          const inX = x >= p.square_x && x < p.square_x + p.square_width
          const inY = y >= p.square_y && y < p.square_y + p.square_height
          return inX && inY
        })
        if (squarePlantings.length > 0) {
          const maxEndDate = squarePlantings.reduce(
            (max, p) => (p.end_date > max ? p.end_date : max),
            squarePlantings[0].end_date
          )
          // Start the day after the last planting ends, but never in the past
          const [yr, mo, dy] = maxEndDate.split('-').map(Number)
          const next = new Date(yr, mo - 1, dy + 1)
          const dayAfterEnd = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}-${String(next.getDate()).padStart(2, '0')}`
          defaultStartDate = dayAfterEnd > todayStr ? dayAfterEnd : todayStr
        }
      }
    } catch {
      // fall back to today
    }

    setPlantingForm({
      start_date: defaultStartDate,
      end_date: '',
      planting_method: '',
      quantity: '',
      square_width: 1,
      square_height: 1,
    })
    fetchVarietiesAndCategories()
    fetchPlantStarts()
  }

  function openStartPicker(x: number, y: number, towerLevel?: number) {
    setStartPickerModal({ x, y, towerLevel })
    setStartPickerCategory(null)
    fetchPlantStarts()
  }

  async function chooseStart(s: PlantStart, modal: { x: number; y: number; towerLevel?: number }) {
    setStartPickerModal(null)
    await openPlantingModal(modal.x, modal.y, modal.towerLevel)
    // openPlantingModal fires its variety fetch without awaiting it — wait for it explicitly
    // here so the auto end-date effect has variety.days_to_harvest data by the time we set
    // selectedVariety below (it bails out silently if `varieties` is still empty).
    await fetchVarietiesAndCategories()
    setSelectedVariety(s.variety_id)
    setSelectedStartId(s.id)
    setPlantingForm(prev => ({
      ...prev,
      planting_method: 'transplant',
      quantity: String(Math.min(1, s.quantity)),
    }))
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
      if (selectedStartId) {
        body.start_id = selectedStartId
      }

      const res = await apiFetch('/api/plantings', {
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
      if (selectedStartId) {
        fetchPlantStarts()
      }
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

  const selectedVarietyObj = varieties.find(v => v.id === selectedVariety) || null

  const matchingStarts = plantStarts.filter((s: PlantStart) => s.variety_id === selectedVariety && s.quantity > 0)

  function selectStart(s: PlantStart) {
    if (selectedStartId === s.id) {
      setSelectedStartId(null)
      return
    }
    setSelectedStartId(s.id)
    setPlantingForm(prev => ({
      ...prev,
      quantity: String(Math.min(Number(prev.quantity) || 1, s.quantity)),
    }))
  }

  function formatStartDate(dateStr: string): string {
    const [yr, mo, dy] = dateStr.split('-').map(Number)
    return new Date(yr, mo - 1, dy).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const activeStarts = plantStarts.filter((s: PlantStart) => s.quantity > 0)
  const startPickerCategories = Array.from(
    new Map(activeStarts.map((s: PlantStart) => [s.category_name || 'Uncategorized', s.category_color || '#ccc'])).entries()
  ).sort((a, b) => a[0].localeCompare(b[0]))
  const filteredStarts = activeStarts.filter(
    (s: PlantStart) => !startPickerCategory || (s.category_name || 'Uncategorized') === startPickerCategory
  )

  function computeNextAvailable(x: number, y: number, towerLevel?: number): string {
    // Find the latest end_date of any planting occupying this square (or tower pocket)
    let maxEnd = todayStr
    for (const p of plantings) {
      if (towerLevel !== undefined && p.tower_level !== towerLevel) continue
      const inX = x >= p.square_x && x < p.square_x + p.square_width
      const inY = y >= p.square_y && y < p.square_y + p.square_height
      if (inX && inY && p.end_date > maxEnd) {
        maxEnd = p.end_date
      }
    }
    return maxEnd
  }

  async function fetchRecommendations(x: number, y: number, towerLevel?: number, dateOverride?: string) {
    const dateToUse = dateOverride ?? computeNextAvailable(x, y, towerLevel)
    setRecDate(dateToUse)
    setRecLoading(true)
    setRecommendations(null)
    setExpandedCategories(new Set())
    setRecSquare({ x, y, towerLevel })
    try {
      const res = await apiFetch(
        `/api/recommendations?container_id=${id}&square_x=${x}&square_y=${y}&date=${dateToUse}` +
          (towerLevel !== undefined ? `&tower_level=${towerLevel}` : '')
      )
      if (!res.ok) throw new Error('Failed to load recommendations')
      setRecommendations(await res.json())
    } catch {
      setRecommendations(null)
    } finally {
      setRecLoading(false)
    }
  }

  function toggleCategory(catId: number) {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(catId)) next.delete(catId)
      else next.add(catId)
      return next
    })
  }

  function handleSquareClick(x: number, y: number) {
    const planting = getPlantingAt(x, y)
    if (planting) {
      setSelectedPlanting(planting)
      setActivateError('')
      setEditingPlanting(false)
      setEditError('')
      setSupportMenu(null)
    } else {
      setSquareChooser({ x, y })
      setSupportMenu(null)
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
            {container.yard_id && (
              <Link to={`/yards/${container.yard_id}`} className="btn btn-outline-dark btn-sm">
                🗺️ View in Yard
              </Link>
            )}
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
          <div className="info-label">Plantings Shown</div>
          <div className="info-value">{plantings.length}</div>
        </div>
      </div>

      {/* Time Slider / Date Picker */}
      <div className="time-slider">
        <button className="time-slider-btn" onClick={() => changeDate(-7)} title="Back 1 week">⏪</button>
        <button className="time-slider-btn" onClick={() => changeDate(-1)} title="Previous day">◀</button>
        <input
          type="date"
          className="time-slider-date"
          value={selectedDate}
          onChange={e => setSelectedDate(e.target.value)}
          autoComplete="off"
          data-1p-ignore
          data-lpignore="true"
          data-form-type="other"
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

      {/* Grid Bed View */}
      {container.type === 'grid_bed' && (
        <div className="detail-section">
          <h3>Garden Bed</h3>
          <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
            Click a square to plant. Right-click for support structures.
          </p>
          <div
            className="grid-bed-wrapper"
            style={{ '--grid-cols': container.width || 5 } as React.CSSProperties}
          >
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
                  const isMulti = planting
                    ? planting.square_width > 1 || planting.square_height > 1
                    : false
                  const isEdgeTop    = planting && y === planting.square_y
                  const isEdgeBottom = planting && y === planting.square_y + planting.square_height - 1
                  const isEdgeLeft   = planting && x === planting.square_x
                  const isEdgeRight  = planting && x === planting.square_x + planting.square_width - 1
                  // Only badge a multi-square planting once, at its top-right corner
                  const nextUp = planting && isEdgeTop && isEdgeRight ? nextUpInfo(planting, selectedDate) : null

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
                        isMulti ? 'is-multi-sq' : '',
                        isMulti && isEdgeTop    ? 'multi-edge-top'    : '',
                        isMulti && isEdgeBottom ? 'multi-edge-bottom' : '',
                        isMulti && isEdgeLeft   ? 'multi-edge-left'   : '',
                        isMulti && isEdgeRight  ? 'multi-edge-right'  : '',
                      ].filter(Boolean).join(' ')}
                      style={planting ? {
                        backgroundColor: (planting.category_color || '#86efac') + '40',
                        borderColor: planting.category_color || undefined,
                        '--group-color': planting.category_color || '#86efac',
                      } as React.CSSProperties : undefined}
                      onClick={() => handleSquareClick(x, y)}
                      onContextMenu={(e) => handleSquareRightClick(e, x, y)}
                      title={
                        planting
                          ? `${planting.variety_name} · ${statusLabel(planting.status)}${planting.overdue ? ' (past estimated end)' : ''}`
                            + (nextUp ? `\n${nextUp.text}` : '')
                          : `${ROW_LABELS[y]}${x + 1}${support ? ` — ${support.support_type}` : ' — empty'}`
                      }
                    >
                      {nextUp && (
                        <span className={`next-up-badge ${nextUp.due ? 'due' : ''}`} aria-label={nextUp.text}>
                          🌱
                        </span>
                      )}
                      {planting && planting.category_icon_svg && (
                        <span
                          className="square-category-icon"
                          dangerouslySetInnerHTML={{ __html: planting.category_icon_svg }}
                        />
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
            <span className="legend-item"><span className="next-up-badge legend">🌱</span> Next planting waiting</span>
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
                    const nextUp = planting ? nextUpInfo(planting, selectedDate) : null
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
                            setActivateError('')
                            setEditingPlanting(false)
                            setEditError('')
                          } else {
                            setSquareChooser({ x: pocket, y: 0, towerLevel: level })
                          }
                        }}
                        title={
                          planting
                            ? (planting.variety_name || '') + (nextUp ? `\n${nextUp.text}` : '')
                            : `Pocket ${pocket + 1}`
                        }
                      >
                        {nextUp && (
                          <span className={`next-up-badge ${nextUp.due ? 'due' : ''}`} aria-label={nextUp.text}>
                            🌱
                          </span>
                        )}
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
                    {statusLabel(p.status)}
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
                {selectedVarietyObj ? (
                  <div className="variety-picker-summary">
                    <span
                      className="variety-picker-dot"
                      style={{ backgroundColor: selectedVarietyObj.category_color || '#ccc' }}
                    />
                    <span className="variety-picker-name">{selectedVarietyObj.name}</span>
                    <span className="variety-picker-category">{selectedVarietyObj.category_name}</span>
                    <button
                      type="button"
                      className="btn-link"
                      onClick={() => {
                        setSelectedVariety(null)
                        setSelectedStartId(null)
                      }}
                    >
                      Change
                    </button>
                  </div>
                ) : (
                  <>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Search varieties..."
                      value={varietySearch}
                      onChange={(e) => setVarietySearch(e.target.value)}
                      autoFocus
                    />

                    {!varietySearch && !selectedCategory && categories.length > 0 && (
                      <div className="category-tile-grid">
                        {categories.map((c: Category) => (
                          <button
                            key={c.id}
                            type="button"
                            className="category-tile"
                            style={{ borderColor: c.color }}
                            onClick={() => setSelectedCategory(c.id)}
                          >
                            <span className="category-tile-dot" style={{ backgroundColor: c.color }} />
                            {c.name}
                          </button>
                        ))}
                      </div>
                    )}

                    {(varietySearch || selectedCategory) && (
                      <>
                        {selectedCategory && (
                          <button
                            type="button"
                            className="chip category-back-chip"
                            onClick={() => setSelectedCategory(null)}
                          >
                            ← {categories.find(c => c.id === selectedCategory)?.name || 'All categories'}
                          </button>
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
                                className="variety-picker-item"
                                onClick={() => {
                                  setSelectedVariety(v.id)
                                  setSelectedStartId(null)
                                }}
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
                      </>
                    )}
                  </>
                )}
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
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
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
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
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
                    onChange={(e) => {
                      const method = e.target.value
                      setPlantingForm({ ...plantingForm, planting_method: method })
                      if (method !== 'transplant') setSelectedStartId(null)
                    }}
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
                    max={selectedStartId ? matchingStarts.find(s => s.id === selectedStartId)?.quantity : undefined}
                    value={plantingForm.quantity}
                    onChange={(e) => {
                      const cap = selectedStartId ? matchingStarts.find(s => s.id === selectedStartId)?.quantity : undefined
                      const raw = e.target.value
                      const clamped = cap && Number(raw) > cap ? String(cap) : raw
                      setPlantingForm({ ...plantingForm, quantity: clamped })
                    }}
                    placeholder="Optional"
                    autoComplete="off"
                    data-1p-ignore
                    data-lpignore="true"
                  />
                </div>
              </div>

              {plantingForm.planting_method === 'transplant' && matchingStarts.length > 0 && (
                <div className="form-group">
                  <label className="form-label">Plant From a Start</label>
                  <div className="variety-picker-list" style={{ maxHeight: '140px' }}>
                    {matchingStarts.map((s: PlantStart) => (
                      <div
                        key={s.id}
                        className={`variety-picker-item ${selectedStartId === s.id ? 'selected' : ''}`}
                        onClick={() => selectStart(s)}
                      >
                        <span className="variety-picker-name">Started {formatStartDate(s.start_date)}</span>
                        <span className="variety-picker-category">{s.quantity} available</span>
                      </div>
                    ))}
                  </div>
                  {selectedStartId && (
                    <p className="text-muted">
                      End date is calculated from this start's seed date, not from Start Date
                      above — Start Date is just when it goes into this square.
                    </p>
                  )}
                </div>
              )}

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

            {editingPlanting ? (
              <form onSubmit={handleUpdatePlanting}>
                {(() => {
                  const target =
                    allContainers.find(c => c.id === editForm.container_id) ??
                    (container?.id === editForm.container_id ? container : null)
                  const range = (n: number) => Array.from({ length: Math.max(n, 0) }, (_, i) => i)
                  return (
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">Container</label>
                        <select
                          className="form-input"
                          value={editForm.container_id}
                          onChange={(e) => setEditContainer(Number(e.target.value))}
                        >
                          {(allContainers.length ? allContainers : container ? [container] : []).map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                          ))}
                        </select>
                      </div>
                      {target?.type === 'tower' ? (
                        <>
                          <div className="form-group">
                            <label className="form-label">Level</label>
                            <select
                              className="form-input"
                              value={editForm.tower_level ?? 0}
                              onChange={(e) => setEditForm({ ...editForm, tower_level: Number(e.target.value) })}
                            >
                              {range(target.levels ?? 0).map(i => (
                                <option key={i} value={i}>{i + 1}</option>
                              ))}
                            </select>
                          </div>
                          <div className="form-group">
                            <label className="form-label">Pocket</label>
                            <select
                              className="form-input"
                              value={editForm.square_x}
                              onChange={(e) => setEditForm({ ...editForm, square_x: Number(e.target.value) })}
                            >
                              {range(target.pockets_per_level ?? 0).map(i => (
                                <option key={i} value={i}>{i + 1}</option>
                              ))}
                            </select>
                          </div>
                        </>
                      ) : target ? (
                        <>
                          <div className="form-group">
                            <label className="form-label">Row</label>
                            <select
                              className="form-input"
                              value={editForm.square_y}
                              onChange={(e) => setEditForm({ ...editForm, square_y: Number(e.target.value) })}
                            >
                              {range((target.height ?? 0) - selectedPlanting.square_height + 1).map(i => (
                                <option key={i} value={i}>{ROW_LABELS[i]}</option>
                              ))}
                            </select>
                          </div>
                          <div className="form-group">
                            <label className="form-label">Column</label>
                            <select
                              className="form-input"
                              value={editForm.square_x}
                              onChange={(e) => setEditForm({ ...editForm, square_x: Number(e.target.value) })}
                            >
                              {range((target.width ?? 0) - selectedPlanting.square_width + 1).map(i => (
                                <option key={i} value={i}>{i + 1}</option>
                              ))}
                            </select>
                          </div>
                        </>
                      ) : null}
                    </div>
                  )
                })()}

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Start Date *</label>
                    <input
                      type="date"
                      className="form-input"
                      value={editForm.start_date}
                      onChange={(e) => setEditForm({ ...editForm, start_date: e.target.value })}
                      required
                      autoComplete="off"
                      data-1p-ignore
                      data-lpignore="true"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">End Date *</label>
                    <input
                      type="date"
                      className="form-input"
                      value={editForm.end_date}
                      onChange={(e) => setEditForm({ ...editForm, end_date: e.target.value })}
                      required
                      autoComplete="off"
                      data-1p-ignore
                      data-lpignore="true"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Seed Started</label>
                    <input
                      type="date"
                      className="form-input"
                      value={editForm.seed_start_date}
                      onChange={(e) => setEditForm({ ...editForm, seed_start_date: e.target.value })}
                      placeholder="If transplanted"
                      autoComplete="off"
                      data-1p-ignore
                      data-lpignore="true"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Method</label>
                    <select
                      className="form-input"
                      value={editForm.planting_method}
                      onChange={(e) => setEditForm({ ...editForm, planting_method: e.target.value })}
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
                      value={editForm.quantity}
                      onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                      placeholder="Optional"
                      autoComplete="off"
                      data-1p-ignore
                      data-lpignore="true"
                    />
                  </div>
                </div>

                {editError && <div className="form-message error">{editError}</div>}

                <div className="modal-actions">
                  <button type="button" className="btn btn-outline-dark" onClick={cancelEditPlanting}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={editSubmitting}>
                    {editSubmitting ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            ) : (
              <>
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
                        {statusLabel(selectedPlanting.status)}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Dates</span>
                      <span className="detail-value">{selectedPlanting.start_date} → {selectedPlanting.end_date}</span>
                    </div>
                    {selectedPlanting.overdue && (() => {
                      const nextUp = nextUpInfo(selectedPlanting, selectedDate)
                      return (
                        <div className={`next-up-note ${nextUp?.due ? 'due' : ''}`}>
                          Past its estimated end date, so it stays in the ground until you mark it done.
                          {nextUp && selectedPlanting.next_planting && (
                            <>
                              <br />
                              <span aria-hidden="true">🌱</span> {nextUp.text}.
                              {' '}
                              <button
                                className="next-up-action"
                                onClick={() => handleActivatePlanting(selectedPlanting.next_planting!)}
                                disabled={activating}
                              >
                                Plant it now
                              </button>
                            </>
                          )}
                        </div>
                      )
                    })()}
                    {selectedPlanting.seed_start_date && (
                      <div className="detail-item">
                        <span className="detail-label">Seed Started</span>
                        <span className="detail-value">{selectedPlanting.seed_start_date}</span>
                      </div>
                    )}
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

                {deleteError && <div className="form-message error">{deleteError}</div>}
                {activateError && !stillGrowing && <div className="form-message error">{activateError}</div>}

                <div className="modal-actions">
                  <button className="btn btn-outline-dark" onClick={startEditPlanting}>
                    ✏️ Edit
                  </button>
                  <Link
                    to={`/plantings/${selectedPlanting.id}`}
                    className="btn btn-outline-dark"
                  >
                    View Details
                  </Link>
                  {selectedPlanting.status === 'not_started' && (
                    <button
                      className="btn btn-primary"
                      onClick={() => handleActivatePlanting(selectedPlanting)}
                      disabled={activating}
                    >
                      {activating ? '…' : '🌱 Plant Now'}
                    </button>
                  )}
                  {selectedPlanting.status === 'in_progress' && (
                    <Link
                      to={`/plantings/${selectedPlanting.id}`}
                      className="btn btn-primary"
                      onClick={() => setSelectedPlanting(null)}
                    >
                      🌾 Log Harvest
                    </Link>
                  )}
                  {selectedPlanting.overdue && (
                    <Link
                      to={`/plantings/${selectedPlanting.id}?remove=1`}
                      className="btn btn-outline-dark"
                      onClick={() => setSelectedPlanting(null)}
                    >
                      ✅ Mark Done
                    </Link>
                  )}
                  <button
                    className="btn btn-outline-dark"
                    title="Plan a successor crop for this square"
                    onClick={() => {
                      const p = selectedPlanting
                      setSelectedPlanting(null)
                      setSquareChooser({
                        x: p.square_x,
                        y: p.square_y ?? 0,
                        towerLevel: p.tower_level ?? undefined,
                      })
                    }}
                  >
                    ➕ Plan Next
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={handleDeletePlanting}
                    disabled={deletingPlanting}
                  >
                    {deletingPlanting ? 'Deleting...' : '🗑️ Delete'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Square Action Chooser Modal */}
      {squareChooser && (
        <div className="modal-overlay" onClick={() => setSquareChooser(null)}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {squareChooser.towerLevel !== undefined
                  ? `Level ${squareChooser.towerLevel + 1}, Pocket ${squareChooser.x + 1}`
                  : `${ROW_LABELS[squareChooser.y]}${squareChooser.x + 1}`}
              </h3>
              <button className="modal-close" onClick={() => setSquareChooser(null)}>✕</button>
            </div>
            <div className="square-chooser-actions">
              <button
                className="square-chooser-btn"
                onClick={() => {
                  const { x, y, towerLevel } = squareChooser
                  setSquareChooser(null)
                  openStartPicker(x, y, towerLevel)
                }}
              >
                <span className="chooser-icon">🌿</span>
                <span className="chooser-label">Plant Something From a Start</span>
                <span className="chooser-desc">Transplant a seedling you've already started</span>
              </button>
              <button
                className="square-chooser-btn"
                onClick={() => {
                  const { x, y, towerLevel } = squareChooser
                  setSquareChooser(null)
                  openPlantingModal(x, y, towerLevel)
                }}
              >
                <span className="chooser-icon">🌱</span>
                <span className="chooser-label">Plant Something</span>
                <span className="chooser-desc">Choose a variety and plant it here</span>
              </button>
              <button
                className="square-chooser-btn"
                onClick={() => {
                  const { x, y, towerLevel } = squareChooser
                  setSquareChooser(null)
                  fetchRecommendations(x, y, towerLevel)
                }}
              >
                <span className="chooser-icon">💡</span>
                <span className="chooser-label">What Can I Plant Here?</span>
                <span className="chooser-desc">Get recommendations based on season & companions</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Start Picker Modal — pick a started seedling, then land in the planting form pre-filled */}
      {startPickerModal && (
        <div className="modal-overlay" onClick={() => setStartPickerModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                Plant From a Start —{' '}
                {startPickerModal.towerLevel !== undefined
                  ? `Level ${startPickerModal.towerLevel + 1}, Pocket ${startPickerModal.x + 1}`
                  : `${ROW_LABELS[startPickerModal.y]}${startPickerModal.x + 1}`}
              </h3>
              <button className="modal-close" onClick={() => setStartPickerModal(null)}>✕</button>
            </div>

            {activeStarts.length === 0 ? (
              <div className="empty-state">
                <span className="empty-icon">🌱</span>
                <h3>No active starts</h3>
                <p>You haven't recorded any started plants yet.</p>
                <Link to="/starts" className="btn btn-primary" onClick={() => setStartPickerModal(null)}>
                  Go to Starts
                </Link>
              </div>
            ) : (
              <>
                {startPickerCategories.length > 1 && (
                  <div className="category-filter-chips">
                    <button
                      type="button"
                      className={`chip ${!startPickerCategory ? 'active' : ''}`}
                      onClick={() => setStartPickerCategory(null)}
                    >
                      All
                    </button>
                    {startPickerCategories.map(([name, color]) => (
                      <button
                        key={name}
                        type="button"
                        className={`chip ${startPickerCategory === name ? 'active' : ''}`}
                        style={startPickerCategory === name ? { backgroundColor: color, color: '#fff' } : undefined}
                        onClick={() => setStartPickerCategory(name)}
                      >
                        {name}
                      </button>
                    ))}
                  </div>
                )}
                <div className="variety-picker-list">
                  {filteredStarts.map((s: PlantStart) => (
                    <div
                      key={s.id}
                      className="variety-picker-item"
                      onClick={() => chooseStart(s, startPickerModal)}
                    >
                      <span
                        className="variety-picker-dot"
                        style={{ backgroundColor: s.category_color || '#ccc' }}
                      />
                      <span className="variety-picker-name">{s.variety_name}</span>
                      <span className="variety-picker-category">
                        Started {formatStartDate(s.start_date)} · {s.quantity} available
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Recommendation Results Modal */}
      {(recommendations || recLoading) && (
        <div className="modal-overlay" onClick={() => { setRecommendations(null); setRecLoading(false); setRecSquare(null) }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <button
                className="btn btn-outline-dark btn-sm"
                style={{ marginRight: 'var(--space-2)' }}
                onClick={() => {
                  setRecommendations(null)
                  setRecLoading(false)
                  if (recSquare) {
                    setSquareChooser(recSquare)
                  }
                  setRecSquare(null)
                }}
                title="Back to options"
              >
                ← Back
              </button>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                <h3 style={{ margin: 0 }}>
                  💡 Recommendations —{' '}
                  {recSquare
                    ? (recSquare.towerLevel !== undefined
                        ? `Level ${recSquare.towerLevel + 1}, Pocket ${recSquare.x + 1}`
                        : `${ROW_LABELS[recSquare.y]}${recSquare.x + 1}`)
                    : recommendations
                      ? `${ROW_LABELS[recommendations.square_y]}${recommendations.square_x + 1}`
                      : '...'}
                </h3>
                <input
                  type="date"
                  className="form-input"
                  style={{ width: 'auto', fontSize: 'var(--text-sm)', padding: '0.2rem 0.5rem' }}
                  value={recDate}
                  onChange={(e) => {
                    if (recSquare) {
                      fetchRecommendations(recSquare.x, recSquare.y, recSquare.towerLevel, e.target.value)
                    }
                  }}
                />
              </div>
              <button className="modal-close" onClick={() => { setRecommendations(null); setRecLoading(false); setRecSquare(null) }}>✕</button>
            </div>

            {recLoading && (
              <div style={{ padding: '2rem', textAlign: 'center' }}>
                <span className="tendril-icon">🌱</span>
                <p>Finding recommendations...</p>
              </div>
            )}

            {recommendations && recommendations.total_varieties === 0 && (
              <div style={{ padding: '2rem', textAlign: 'center' }}>
                <span style={{ fontSize: '2rem' }}>🤷</span>
                <p>No varieties match this square right now.</p>
                <p className="text-muted">Try a different date or add more varieties to your catalog.</p>
              </div>
            )}

            {recommendations && recommendations.total_varieties > 0 && (
              <div className="rec-results">
                <p className="text-muted" style={{ marginBottom: 'var(--space-3)' }}>
                  {recommendations.total_varieties} varieties in {recommendations.categories.length} categories
                </p>
                {recommendations.categories.map(cat => (
                  <div key={cat.category_id} className="rec-category">
                    <button
                      className="rec-category-header"
                      onClick={() => toggleCategory(cat.category_id)}
                    >
                      <span
                        className="rec-category-dot"
                        style={{ backgroundColor: cat.category_color }}
                      />
                      <span className="rec-category-name">{cat.category_name}</span>
                      <span className="rec-category-count">{cat.varieties.length}</span>
                      <span className="rec-category-arrow">
                        {expandedCategories.has(cat.category_id) ? '▼' : '▶'}
                      </span>
                    </button>
                    {expandedCategories.has(cat.category_id) && (
                      <div className="rec-variety-list">
                        {cat.varieties.map(v => (
                          <div
                            key={v.variety_id}
                            className="rec-variety-item"
                            onClick={() => {
                              setRecommendations(null)
                              setSelectedVariety(v.variety_id)
                              if (recommendations) {
                                openPlantingModal(
                                  recommendations.square_x,
                                  recommendations.square_y,
                                  recommendations.tower_level ?? undefined,
                                )
                                // Pre-select the variety
                                setTimeout(() => setSelectedVariety(v.variety_id), 50)
                              }
                            }}
                          >
                            <div className="rec-variety-header">
                              <strong>{v.variety_name}</strong>
                              <span className="rec-score">Score: {v.score}</span>
                            </div>
                            <div className="rec-variety-meta">
                              {v.days_to_harvest_min && (
                                <span>🕐 {v.days_to_harvest_min}–{v.days_to_harvest_max || '?'} days</span>
                              )}
                              <span>📐 {v.spacing}</span>
                              {v.is_climbing && <span>🧗 Climbing</span>}
                              <span>🌱 {v.planting_method.replace('_', ' ')}</span>
                            </div>
                            {v.boosts.length > 0 && (
                              <div className="rec-boosts">
                                {v.boosts.map((b, i) => (
                                  <span key={i} className="rec-boost">✅ {b}</span>
                                ))}
                              </div>
                            )}
                            {v.warnings.length > 0 && (
                              <div className="rec-warnings">
                                {v.warnings.map((w, i) => (
                                  <span key={i} className="rec-warning">⚠️ {w}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {stillGrowing && (
        <StillGrowingModal
          newVarietyName={stillGrowing.planting.variety_name}
          stillGrowing={stillGrowing.growing}
          busy={activating}
          error={activateError}
          onConfirm={reason => handleActivatePlanting(stillGrowing.planting, reason)}
          onCancel={() => setStillGrowing(null)}
        />
      )}
    </div>
  )
}
