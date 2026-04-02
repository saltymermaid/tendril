/**
 * GanttChart — Custom SVG Gantt chart for planting timelines.
 *
 * Two view modes:
 *   - groupBy 'square'    : one row per grid square (e.g. "D3"), showing all
 *                           plantings for that square as sequential bars.
 *                           Empty squares shown as blank rows.
 *                           Multi-square plantings appear on every square they cover.
 *   - groupBy 'container' : one row per planting, grouped under container headers.
 *   - groupBy 'none'      : one row per planting, flat list.
 *
 * Bar segments (3 lifecycle phases):
 *   - Germination (lightest shade)
 *   - Growing     (medium shade)
 *   - Harvesting  (full category color)
 *
 * Features:
 *   - Horizontal scrolling for time navigation
 *   - Today marker (vertical red line)
 *   - Month grid lines
 *   - Click a bar to navigate to planting detail
 *   - Status-based visual treatments (not_started=dashed, complete=muted)
 *   - Variety name label rendered on each bar (square view)
 */

import { useNavigate } from 'react-router-dom'
import type { JSX } from 'react'

export interface TimelinePlanting {
  id: number
  container_id: number
  container_name: string | null
  variety_id: number
  variety_name: string | null
  category_name: string | null
  category_color: string | null
  category_icon_svg: string | null
  start_date: string
  end_date: string
  germination_end: string
  harvest_start: string
  status: string
  square_x: number
  square_y: number
  tower_level: number | null
  /** for multi-square plantings, the actual width/height */
  square_width?: number
  square_height?: number
}

export interface ContainerInfo {
  id: number
  name: string
  type: string
  width: number | null
  height: number | null
  levels: number | null
  pockets_per_level: number | null
}

interface GanttChartProps {
  plantings: TimelinePlanting[]
  containers: ContainerInfo[]
  startDate: string
  endDate: string
  groupBy: 'container' | 'square' | 'none'
}

const ROW_HEIGHT = 32
const ROW_GAP = 4
const HEADER_HEIGHT = 48
const LEFT_LABEL_WIDTH = 180
const DAY_WIDTH = 4 // pixels per day
const GROUP_HEADER_HEIGHT = 28
const ROW_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

function squareLabel(x: number, y: number, containerType: string, towerLevel: number | null): string {
  if (containerType === 'tower' && towerLevel !== null) {
    return `L${towerLevel + 1}P${x + 1}`
  }
  return `${ROW_LABELS[y] ?? y}${x + 1}`
}

function statusLabel(status: string): string {
  if (status === 'not_started') return 'Planned'
  if (status === 'in_progress') return 'Growing'
  if (status === 'complete') return 'Done'
  return status
}

function parseDate(s: string): Date {
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24))
}

function lightenColor(hex: string, amount: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const nr = Math.min(255, Math.round(r + (255 - r) * amount))
  const ng = Math.min(255, Math.round(g + (255 - g) * amount))
  const nb = Math.min(255, Math.round(b + (255 - b) * amount))
  return `#${nr.toString(16).padStart(2, '0')}${ng.toString(16).padStart(2, '0')}${nb.toString(16).padStart(2, '0')}`
}

function muteColor(hex: string): string {
  return lightenColor(hex, 0.4)
}

/** Render a single planting bar (3 phase segments) at given y position */
function renderBar(
  p: TimelinePlanting,
  currentY: number,
  rangeStart: Date,
  totalDays: number,
  navigate: (path: string) => void,
  showVarietyLabel: boolean,
  key: string,
): JSX.Element {
  const color = p.category_color || '#888888'
  const pStart = parseDate(p.start_date)
  const pEnd = parseDate(p.end_date)
  const germEnd = parseDate(p.germination_end)
  const harvestStart = parseDate(p.harvest_start)

  const barStartDay = Math.max(0, daysBetween(rangeStart, pStart))
  const barEndDay = Math.min(totalDays, daysBetween(rangeStart, pEnd))
  const barX = LEFT_LABEL_WIDTH + barStartDay * DAY_WIDTH
  const barWidth = Math.max(2, (barEndDay - barStartDay) * DAY_WIDTH)

  const germEndDay = Math.max(0, Math.min(barEndDay, daysBetween(rangeStart, germEnd)))
  const harvestStartDay = Math.max(0, Math.min(barEndDay, daysBetween(rangeStart, harvestStart)))

  const germX = barX
  const germW = Math.max(0, (germEndDay - barStartDay) * DAY_WIDTH)
  const growX = germX + germW
  const growW = Math.max(0, (harvestStartDay - germEndDay) * DAY_WIDTH)
  const harvestX = growX + growW
  const harvestW = Math.max(0, barWidth - germW - growW)

  let germColor = lightenColor(color, 0.6)
  let growColor = lightenColor(color, 0.3)
  let harvestColor = color
  let opacity = 1
  let strokeDash = ''

  if (p.status === 'not_started') {
    opacity = 0.6
    strokeDash = '4,2'
  } else if (p.status === 'complete') {
    germColor = muteColor(germColor)
    growColor = muteColor(growColor)
    harvestColor = muteColor(harvestColor)
    opacity = 0.8
  }

  const barTop = currentY + 4
  const barH = ROW_HEIGHT - 8

  // Variety name label — only if bar is wide enough (> 30px) and requested
  const varietyName = p.variety_name ?? ''
  const labelMinWidth = 30
  const labelText = showVarietyLabel && barWidth > labelMinWidth
    ? (barWidth > 80 ? varietyName : varietyName.slice(0, Math.floor(barWidth / 7)))
    : ''

  return (
    <g
      key={key}
      style={{ cursor: 'pointer' }}
      onClick={() => navigate(`/plantings/${p.id}`)}
    >
      <title>{statusLabel(p.status)} · {p.variety_name ?? 'Unknown'} · {p.start_date} – {p.end_date}</title>
      {/* Bar outline */}
      <rect
        x={barX}
        y={barTop}
        width={barWidth}
        height={barH}
        rx={3}
        ry={3}
        fill="none"
        stroke={color}
        strokeWidth={1}
        strokeDasharray={strokeDash}
        opacity={opacity}
      />
      {/* Germination segment */}
      {germW > 0 && (
        <rect x={germX} y={barTop} width={germW} height={barH} rx={3} ry={3}
          fill={germColor} opacity={opacity} />
      )}
      {/* Growing segment */}
      {growW > 0 && (
        <rect x={growX} y={barTop} width={growW} height={barH}
          fill={growColor} opacity={opacity} />
      )}
      {/* Harvesting segment */}
      {harvestW > 0 && (
        <rect x={harvestX} y={barTop} width={harvestW} height={barH} rx={3} ry={3}
          fill={harvestColor} opacity={opacity} />
      )}
      {/* Variety name on bar */}
      {labelText && (
        <text
          x={barX + 4}
          y={currentY + ROW_HEIGHT / 2 + 4}
          fontSize="10"
          fill="rgba(255,255,255,0.9)"
          style={{ pointerEvents: 'none', fontWeight: 600 }}
        >
          {labelText}
        </text>
      )}
    </g>
  )
}

export function GanttChart({ plantings, containers, startDate, endDate, groupBy }: GanttChartProps) {
  const navigate = useNavigate()
  const rangeStart = parseDate(startDate)
  const rangeEnd = parseDate(endDate)
  const totalDays = daysBetween(rangeStart, rangeEnd)
  const chartWidth = totalDays * DAY_WIDTH

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayOffset = daysBetween(rangeStart, today)

  // Build a lookup from container_id to ContainerInfo
  const containerMap = new Map<number, ContainerInfo>()
  for (const c of containers) {
    containerMap.set(c.id, c)
  }

  // ─── SQUARE VIEW ──────────────────────────────────────────────────────────
  type SquareKey = string // `${container_id}-${x}-${y}` (or `${container_id}-t${level}-${pocket}` for towers)
  type SquareRow = {
    containerInfo: ContainerInfo
    squareX: number
    squareY: number
    towerLevel: number | null
    label: string
    plantingsForSquare: TimelinePlanting[]
  }

  let squareRows: SquareRow[] = []

  if (groupBy === 'square') {
    // For each container, enumerate all squares
    // Determine which containers are in scope (all, or just the ones referenced)
    const referencedContainerIds = new Set(plantings.map(p => p.container_id))
    // Use containers prop; if "all containers", show all; if filtered, the containers prop
    // will have all containers loaded (TimelinePage always loads all containers)
    const containersToShow = containers.filter(c =>
      referencedContainerIds.has(c.id) || containers.length <= 1
    )

    // Build map: squareKey → plantings
    const squarePlantings = new Map<SquareKey, TimelinePlanting[]>()

    for (const p of plantings) {
      const sw = p.square_width ?? 1
      const sh = p.square_height ?? 1
      // For towers
      if (p.tower_level !== null) {
        const key: SquareKey = `${p.container_id}-t${p.tower_level}-${p.square_x}`
        if (!squarePlantings.has(key)) squarePlantings.set(key, [])
        squarePlantings.get(key)!.push(p)
      } else {
        // Expand multi-square plantings to all covered squares
        for (let dy = 0; dy < sh; dy++) {
          for (let dx = 0; dx < sw; dx++) {
            const key: SquareKey = `${p.container_id}-${p.square_x + dx}-${p.square_y + dy}`
            if (!squarePlantings.has(key)) squarePlantings.set(key, [])
            squarePlantings.get(key)!.push(p)
          }
        }
      }
    }

    // Build ordered list of all squares for each container
    for (const c of containersToShow) {
      if (c.type === 'tower' && c.levels != null && c.pockets_per_level != null) {
        for (let level = 0; level < c.levels; level++) {
          for (let pocket = 0; pocket < c.pockets_per_level; pocket++) {
            const key: SquareKey = `${c.id}-t${level}-${pocket}`
            squareRows.push({
              containerInfo: c,
              squareX: pocket,
              squareY: 0,
              towerLevel: level,
              label: squareLabel(pocket, 0, 'tower', level),
              plantingsForSquare: squarePlantings.get(key) ?? [],
            })
          }
        }
      } else if (c.type === 'grid_bed' && c.width != null && c.height != null) {
        for (let y = 0; y < c.height; y++) {
          for (let x = 0; x < c.width; x++) {
            const key: SquareKey = `${c.id}-${x}-${y}`
            squareRows.push({
              containerInfo: c,
              squareX: x,
              squareY: y,
              towerLevel: null,
              label: squareLabel(x, y, 'grid_bed', null),
              plantingsForSquare: squarePlantings.get(key) ?? [],
            })
          }
        }
      }
    }

    // If no containers match (e.g. fresh load), fall back to plantings-derived squares
    if (squareRows.length === 0 && plantings.length > 0) {
      // Just show squares from plantings
      const seen = new Set<string>()
      for (const p of plantings) {
        const c = containerMap.get(p.container_id)
        if (!c) continue
        const sw = p.square_width ?? 1
        const sh = p.square_height ?? 1
        if (p.tower_level !== null) {
          const key = `${p.container_id}-t${p.tower_level}-${p.square_x}`
          if (!seen.has(key)) {
            seen.add(key)
            squareRows.push({
              containerInfo: c,
              squareX: p.square_x,
              squareY: 0,
              towerLevel: p.tower_level,
              label: squareLabel(p.square_x, 0, 'tower', p.tower_level),
              plantingsForSquare: [p],
            })
          }
        } else {
          for (let dy = 0; dy < sh; dy++) {
            for (let dx = 0; dx < sw; dx++) {
              const key = `${p.container_id}-${p.square_x + dx}-${p.square_y + dy}`
              if (!seen.has(key)) {
                seen.add(key)
                squareRows.push({
                  containerInfo: c,
                  squareX: p.square_x + dx,
                  squareY: p.square_y + dy,
                  towerLevel: null,
                  label: squareLabel(p.square_x + dx, p.square_y + dy, 'grid_bed', null),
                  plantingsForSquare: [],
                })
              }
              // Add planting to the right row
              const row = squareRows.find(r => r.squareX === p.square_x + dx && r.squareY === p.square_y + dy && r.containerInfo.id === p.container_id)
              if (row && !row.plantingsForSquare.includes(p)) row.plantingsForSquare.push(p)
            }
          }
        }
      }
    }
  }

  // ─── CONTAINER / NONE VIEW ────────────────────────────────────────────────
  type GroupedRow = { label: string; planting: TimelinePlanting }
  const plantingRows: (GroupedRow | { groupLabel: string })[] = []

  if (groupBy === 'container') {
    const groups: Record<number, TimelinePlanting[]> = {}
    const groupOrder: number[] = []
    for (const p of plantings) {
      if (!groups[p.container_id]) {
        groups[p.container_id] = []
        groupOrder.push(p.container_id)
      }
      groups[p.container_id].push(p)
    }
    for (const cid of groupOrder) {
      const containerName = groups[cid][0]?.container_name || `Container ${cid}`
      plantingRows.push({ groupLabel: containerName })
      for (const p of groups[cid]) {
        plantingRows.push({ label: p.variety_name || 'Unknown', planting: p })
      }
    }
  } else if (groupBy === 'none') {
    for (const p of plantings) {
      plantingRows.push({ label: p.variety_name || 'Unknown', planting: p })
    }
  }

  // ─── HEIGHT CALCULATION ───────────────────────────────────────────────────
  let totalHeight = HEADER_HEIGHT

  if (groupBy === 'square') {
    // Check if we need container group headers (more than one container in view)
    const uniqueContainerIds = new Set(squareRows.map(r => r.containerInfo.id))
    const showContainerHeaders = uniqueContainerIds.size > 1

    if (showContainerHeaders) {
      let prevCid = -1
      for (const row of squareRows) {
        if (row.containerInfo.id !== prevCid) {
          totalHeight += GROUP_HEADER_HEIGHT
          prevCid = row.containerInfo.id
        }
        totalHeight += ROW_HEIGHT + ROW_GAP
      }
    } else {
      totalHeight += squareRows.length * (ROW_HEIGHT + ROW_GAP)
    }
  } else {
    for (const row of plantingRows) {
      if ('groupLabel' in row) {
        totalHeight += GROUP_HEADER_HEIGHT
      } else {
        totalHeight += ROW_HEIGHT + ROW_GAP
      }
    }
  }
  totalHeight = Math.max(totalHeight, HEADER_HEIGHT + 60)

  // ─── MONTH MARKERS ────────────────────────────────────────────────────────
  const months: { x: number; label: string }[] = []
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const cursor = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), 1)
  while (cursor <= rangeEnd) {
    const offset = daysBetween(rangeStart, cursor)
    if (offset >= 0) {
      months.push({
        x: LEFT_LABEL_WIDTH + offset * DAY_WIDTH,
        label: `${monthNames[cursor.getMonth()]} ${cursor.getFullYear()}`,
      })
    }
    cursor.setMonth(cursor.getMonth() + 1)
  }

  // ─── RENDER ROWS ─────────────────────────────────────────────────────────
  let currentY = HEADER_HEIGHT
  const renderedRows: JSX.Element[] = []

  if (groupBy === 'square') {
    const uniqueContainerIds = new Set(squareRows.map(r => r.containerInfo.id))
    const showContainerHeaders = uniqueContainerIds.size > 1
    let prevCid = -1
    let rowIdx = 0

    for (const squareRow of squareRows) {
      // Container group header
      if (showContainerHeaders && squareRow.containerInfo.id !== prevCid) {
        prevCid = squareRow.containerInfo.id
        renderedRows.push(
          <g key={`grp-${squareRow.containerInfo.id}`}>
            <rect
              x={0} y={currentY}
              width={LEFT_LABEL_WIDTH + chartWidth}
              height={GROUP_HEADER_HEIGHT}
              fill="var(--color-gray-100)"
            />
            <text
              x={8} y={currentY + GROUP_HEADER_HEIGHT / 2 + 4}
              fontSize="12" fontWeight="600" fill="var(--color-text)"
            >
              {squareRow.containerInfo.name}
            </text>
          </g>
        )
        currentY += GROUP_HEADER_HEIGHT
      }

      const rowBg = rowIdx % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.02)'
      const isEmpty = squareRow.plantingsForSquare.length === 0

      renderedRows.push(
        <g key={`sq-${squareRow.containerInfo.id}-${squareRow.squareX}-${squareRow.squareY}-${squareRow.towerLevel}`}>
          {/* Row background */}
          <rect
            x={0} y={currentY}
            width={LEFT_LABEL_WIDTH + chartWidth}
            height={ROW_HEIGHT}
            fill={rowBg}
          />
          {/* Square label */}
          <text
            x={8}
            y={currentY + ROW_HEIGHT / 2 + 4}
            fontSize="11"
            fontWeight="600"
            fill={isEmpty ? 'var(--color-text-muted, #aaa)' : 'var(--color-text-secondary)'}
          >
            {squareRow.label}
          </text>
          {/* Empty indicator */}
          {isEmpty && (
            <text
              x={40}
              y={currentY + ROW_HEIGHT / 2 + 4}
              fontSize="10"
              fill="var(--color-text-muted, #ccc)"
              fontStyle="italic"
            >
              empty
            </text>
          )}
          {/* Planting bars */}
          {squareRow.plantingsForSquare.map(p =>
            renderBar(
              p,
              currentY,
              rangeStart,
              totalDays,
              navigate,
              true, // show variety label
              `bar-${squareRow.containerInfo.id}-${squareRow.squareX}-${squareRow.squareY}-${p.id}`,
            )
          )}
        </g>
      )

      currentY += ROW_HEIGHT + ROW_GAP
      rowIdx++
    }

    // If no containers/squares to show at all
    if (squareRows.length === 0) {
      renderedRows.push(
        <text key="empty" x={LEFT_LABEL_WIDTH + 16} y={HEADER_HEIGHT + 30}
          fontSize="13" fill="var(--color-text-secondary)">
          No plantings in this range
        </text>
      )
    }
  } else {
    // Original planting-per-row rendering
    for (let i = 0; i < plantingRows.length; i++) {
      const row = plantingRows[i]

      if ('groupLabel' in row) {
        renderedRows.push(
          <g key={`group-${i}`}>
            <rect
              x={0} y={currentY}
              width={LEFT_LABEL_WIDTH + chartWidth}
              height={GROUP_HEADER_HEIGHT}
              fill="var(--color-gray-100)"
            />
            <text
              x={8} y={currentY + GROUP_HEADER_HEIGHT / 2 + 4}
              fontSize="12" fontWeight="600" fill="var(--color-text)"
            >
              {row.groupLabel}
            </text>
          </g>
        )
        currentY += GROUP_HEADER_HEIGHT
        continue
      }

      const p = row.planting
      const rowBg = i % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.02)'

      renderedRows.push(
        <g key={`row-${p.id}`}>
          {/* Row background */}
          <rect
            x={0} y={currentY}
            width={LEFT_LABEL_WIDTH + chartWidth}
            height={ROW_HEIGHT}
            fill={rowBg}
          />
          {/* Category icon */}
          {p.category_icon_svg && (
            <foreignObject
              x={8} y={currentY + ROW_HEIGHT / 2 - 8}
              width={16} height={16}
            >
              <div
                style={{ width: 16, height: 16, overflow: 'hidden', lineHeight: '16px' }}
                dangerouslySetInnerHTML={{ __html: p.category_icon_svg }}
              />
            </foreignObject>
          )}
          {/* Label */}
          <text
            x={p.category_icon_svg ? 28 : 8}
            y={currentY + ROW_HEIGHT / 2 + 4}
            fontSize="11"
            fill="var(--color-text-secondary)"
          >
            {(() => {
              const maxChars = p.category_icon_svg ? 18 : 22
              return row.label.length > maxChars ? row.label.slice(0, maxChars - 2) + '…' : row.label
            })()}
          </text>
          {/* Planting bar */}
          {renderBar(p, currentY, rangeStart, totalDays, navigate, false, `bar-${p.id}`)}
        </g>
      )

      currentY += ROW_HEIGHT + ROW_GAP
    }
  }

  const svgWidth = LEFT_LABEL_WIDTH + chartWidth

  return (
    <div className="gantt-wrapper">
      <div className="gantt-scroll-container">
        <svg width={svgWidth} height={totalHeight} className="gantt-svg">
          {/* Header background */}
          <rect x={0} y={0} width={svgWidth} height={HEADER_HEIGHT} fill="var(--color-gray-50)" />

          {/* Month grid lines and labels */}
          {months.map((m, i) => (
            <g key={`month-${i}`}>
              <line
                x1={m.x} y1={HEADER_HEIGHT} x2={m.x} y2={totalHeight}
                stroke="var(--color-gray-200)" strokeWidth={1}
              />
              <text
                x={m.x + 4} y={HEADER_HEIGHT - 8}
                fontSize="11" fill="var(--color-text-secondary)"
              >
                {m.label}
              </text>
            </g>
          ))}

          {/* Left label column separator */}
          <line
            x1={LEFT_LABEL_WIDTH} y1={0} x2={LEFT_LABEL_WIDTH} y2={totalHeight}
            stroke="var(--color-gray-200)" strokeWidth={1}
          />

          {/* Rows */}
          {renderedRows}

          {/* Today marker */}
          {todayOffset >= 0 && todayOffset <= totalDays && (
            <g>
              <line
                x1={LEFT_LABEL_WIDTH + todayOffset * DAY_WIDTH} y1={HEADER_HEIGHT}
                x2={LEFT_LABEL_WIDTH + todayOffset * DAY_WIDTH} y2={totalHeight}
                stroke="#E53E3E" strokeWidth={2} strokeDasharray="4,4"
              />
              <text
                x={LEFT_LABEL_WIDTH + todayOffset * DAY_WIDTH + 4}
                y={HEADER_HEIGHT + 14}
                fontSize="10" fill="#E53E3E" fontWeight="600"
              >
                Today
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Legend */}
      <div className="gantt-legend">
        <div className="gantt-legend-item">
          <span className="gantt-legend-swatch" style={{ background: lightenColor('#38A169', 0.6) }} />
          Germination
        </div>
        <div className="gantt-legend-item">
          <span className="gantt-legend-swatch" style={{ background: lightenColor('#38A169', 0.3) }} />
          Growing
        </div>
        <div className="gantt-legend-item">
          <span className="gantt-legend-swatch" style={{ background: '#38A169' }} />
          Harvesting
        </div>
        <div className="gantt-legend-item">
          <span className="gantt-legend-swatch gantt-legend-dashed" />
          Not Started
        </div>
        <div className="gantt-legend-item">
          <span className="gantt-legend-line" />
          Today
        </div>
      </div>
    </div>
  )
}
