import { useState } from 'react'
import { REMOVAL_REASONS, type StillGrowing } from '../lib/plantings'

interface StillGrowingModalProps {
  /** The planned planting about to go in */
  newVarietyName: string | null
  stillGrowing: StillGrowing[]
  busy: boolean
  error?: string
  onConfirm: (removalReason: string) => void
  onCancel: () => void
}

/** Shown when "Plant Now" hits a square that still has an earlier planting growing in it. */
export function StillGrowingModal({ newVarietyName, stillGrowing, busy, error, onConfirm, onCancel }: StillGrowingModalProps) {
  const [reason, setReason] = useState('')
  const names = stillGrowing.map(p => p.variety_name ?? 'An earlier planting').join(' and ')
  const plural = stillGrowing.length > 1

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{names} {plural ? 'are' : 'is'} still growing here</h3>
          <button className="modal-close" onClick={onCancel}>×</button>
        </div>
        <div className="planting-detail-body">
          <p className="text-muted" style={{ marginBottom: '1rem' }}>
            Mark {plural ? 'them' : 'it'} done and plant {newVarietyName ?? 'this'}? Why did {plural ? 'they' : 'it'} come out?
          </p>
          <div className="removal-reason-list">
            {REMOVAL_REASONS.map(r => (
              <button
                key={r.value}
                className={`removal-reason-btn ${reason === r.value ? 'selected' : ''}`}
                onClick={() => setReason(r.value)}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
        {error && <div className="form-message error">{error}</div>}
        <div className="modal-actions">
          <button className="btn btn-primary" disabled={!reason || busy} onClick={() => onConfirm(reason)}>
            {busy ? '…' : '✅ Mark Done & Plant'}
          </button>
          <button className="btn btn-outline-dark" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  )
}
