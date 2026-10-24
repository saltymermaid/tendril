import { apiFetch } from './api'

// Why a planting came out of the ground (Planting.removal_reason)
export const REMOVAL_REASONS = [
  { value: 'harvest_complete', label: '🌾 Harvest Complete' },
  { value: 'died', label: '💀 Died' },
  { value: 'pulled_early', label: '🔄 Pulled Early' },
  { value: 'pest_disease', label: '🐛 Pest / Disease' },
  { value: 'other', label: '📝 Other' },
]

/** An earlier planting still growing on the squares a planned planting is going into. */
export interface StillGrowing {
  id: number
  variety_name: string | null
  start_date: string
}

export type ActivateResult<T> =
  | { ok: true; planting: T }
  | { ok: false; stillGrowing: StillGrowing[] }
  | { ok: false; error: string }

/**
 * Mark a planned planting as planted. If something's still growing on its squares the
 * backend refuses with `stillGrowing` — retry with `replaceReason` to mark those done too.
 */
export async function activatePlanting<T>(id: number | string, replaceReason?: string): Promise<ActivateResult<T>> {
  const res = await apiFetch(`/api/plantings/${id}/activate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(replaceReason ? { replace_reason: replaceReason } : {}),
  })
  if (res.ok) return { ok: true, planting: await res.json() }
  const data = await res.json().catch(() => ({}))
  if (res.status === 409 && data.detail?.still_growing) {
    return { ok: false, stillGrowing: data.detail.still_growing }
  }
  const detail = typeof data.detail === 'string' ? data.detail : data.detail?.message
  return { ok: false, error: detail || 'Failed to mark as planted' }
}
