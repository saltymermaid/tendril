/**
 * GanttChart — Custom SVG Gantt chart for planting timelines.
 *
 * Renders planting bars with three lifecycle phase segments:
 *   - Germination (lightest shade)
 *   - Growing (medium shade)
 *   - Harvesting (full category color)
 *
 * Features:
 *   - Horizontal scrolling for time navigation
 *   - Today marker (vertical red line)
 *   - Month grid lines
 *   - Click a bar to navigate to planting detail
 *   - Status-based visual treatments (not_started=dashed, complete=muted)
 */

import { useNavigate } from 'react-router-dom'

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
}

interface GanttChartProps {
  plantings: TimelinePlanting[]
  startDate: string
  endDate: string
  groupBy: 'container' | 'none'
}

const ROW_HEIGHT = 32
const ROW_GAP = 4
const HEADER_HEIGHT = 48
const LEFT_LABEL_WIDTH = 180
const DAY_WIDTH = 4 // pixels per day
const GROUP_HEADER_HEIGHT = 28

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
  // Convert hex to RGB, lighten, convert back
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

export function GanttChart({ plantings, startDate, endDate, groupBy }: GanttChartProps) {
  const navigate = useNavigate()
  const rangeStart = parseDate(startDate)
  const rangeEnd = parseDate(endDate)
  const totalDays = daysBetween(rangeStart, rangeEnd)
  const chartWidth = totalDays * DAY_WIDTH

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayOffset = daysBetween(rangeStart, today)

  // Group plantings by container if needed
  type GroupedRow = { label: string; planting: TimelinePlanting }
  const rows: (GroupedRow | { groupLabel: string })[] = []

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
      rows.push({ groupLabel: containerName })
      for (const p of groups[cid]) {
        const label = p.variety_name || 'Unknown'
        rows.push({ label, planting: p })
      }
    }
  } else {
    for (const p of plantings) {
      const label = p.variety_name || 'Unknown'
      rows.push({ label, planting: p })
    }
  }

  // Calculate total height
  let totalHeight = HEADER_HEIGHT
  for (const row of rows) {
    if ('groupLabel' in row) {
      totalHeight += GROUP_HEADER_HEIGHT
    } else {
      totalHeight += ROW_HEIGHT + ROW_GAP
    }
  }
  totalHeight = Math.max(totalHeight, HEADER_HEIGHT + 60)

  // Generate month markers
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

  // Render rows
  let currentY = HEADER_HEIGHT
  const renderedRows: JSX.Element[] = []

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]

    if ('groupLabel' in row) {
      // Group header
      renderedRows.push(
        <g key={`group-${i}`}>
          <rect
            x={0}
            y={currentY}
            width={LEFT_LABEL_WIDTH + chartWidth}
            height={GROUP_HEADER_HEIGHT}
            fill="var(--color-gray-100)"
          />
          <text
            x={8}
            y={currentY + GROUP_HEADER_HEIGHT / 2 + 4}
            fontSize="12"
            fontWeight="600"
            fill="var(--color-text)"
          >
            {row.groupLabel}
          </text>
        </g>
      )
      currentY += GROUP_HEADER_HEIGHT
      continue
    }

    const p = row.planting
    const color = p.category_color || '#888888'
    const pStart = parseDate(p.start_date)
    const pEnd = parseDate(p.end_date)
    const germEnd = parseDate(p.germination_end)
    const harvestStart = parseDate(p.harvest_start)

    const barStartDay = Math.max(0, daysBetween(rangeStart, pStart))
    const barEndDay = Math.min(totalDays, daysBetween(rangeStart, pEnd))
    const barX = LEFT_LABEL_WIDTH + barStartDay * DAY_WIDTH
    const barWidth = Math.max(2, (barEndDay - barStartDay) * DAY_WIDTH)

    // Phase boundaries relative to planting start
    const germEndDay = Math.max(0, Math.min(barEndDay, daysBetween(rangeStart, germEnd)))
    const harvestStartDay = Math.max(0, Math.min(barEndDay, daysBetween(rangeStart, harvestStart)))

    // Phase widths
    const germX = barX
    const germW = Math.max(0, (germEndDay - barStartDay) * DAY_WIDTH)
    const growX = germX + germW
    const growW = Math.max(0, (harvestStartDay - germEndDay) * DAY_WIDTH)
    const harvestX = growX + growW
    const harvestW = Math.max(0, barWidth - germW - growW)

    // Colors based on status
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

    // Alternating row background
    const rowBg = i % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.02)'

    renderedRows.push(
      <g
        key={`row-${p.id}`}
        style={{ cursor: 'pointer' }}
        onClick={() => navigate(`/plantings/${p.id}`)}
      >
        <title>{statusLabel(p.status)} · {p.variety_name ?? 'Unknown'} · {p.start_date} – {p.end_date}</title>
        {/* Row background */}
        <rect
          x={0}
          y={currentY}
          width={LEFT_LABEL_WIDTH + chartWidth}
          height={ROW_HEIGHT}
          fill={rowBg}
        />
        {/* Category icon */}
        {p.category_icon_svg && (
          <foreignObject
            x={8}
            y={currentY + ROW_HEIGHT / 2 - 8}
            width={16}
            height={16}
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
        {/* Bar outline */}
        <rect
          x={barX}
          y={currentY + 4}
          width={barWidth}
          height={ROW_HEIGHT - 8}
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
          <rect
            x={germX}
            y={currentY + 4}
            width={germW}
            height={ROW_HEIGHT - 8}
            rx={3}
            ry={3}
            fill={germColor}
            opacity={opacity}
          />
        )}
        {/* Growing segment */}
        {growW > 0 && (
          <rect
            x={growX}
            y={currentY + 4}
            width={growW}
            height={ROW_HEIGHT - 8}
            fill={growColor}
            opacity={opacity}
          />
        )}
        {/* Harvesting segment */}
        {harvestW > 0 && (
          <rect
            x={harvestX}
            y={currentY + 4}
            width={harvestW}
            height={ROW_HEIGHT - 8}
            rx={3}
            ry={3}
            fill={harvestColor}
            opacity={opacity}
          />
        )}
      </g>
    )

    currentY += ROW_HEIGHT + ROW_GAP
  }

  const svgWidth = LEFT_LABEL_WIDTH + chartWidth

  return (
    <div className="gantt-wrapper">
      <div className="gantt-scroll-container">
        <svg
          width={svgWidth}
          height={totalHeight}
          className="gantt-svg"
        >
          {/* Header background */}
          <rect x={0} y={0} width={svgWidth} height={HEADER_HEIGHT} fill="var(--color-gray-50)" />

          {/* Month grid lines and labels */}
          {months.map((m, i) => (
            <g key={`month-${i}`}>
              <line
                x1={m.x}
                y1={HEADER_HEIGHT}
                x2={m.x}
                y2={totalHeight}
                stroke="var(--color-gray-200)"
                strokeWidth={1}
              />
              <text
                x={m.x + 4}
                y={HEADER_HEIGHT - 8}
                fontSize="11"
                fill="var(--color-text-secondary)"
              >
                {m.label}
              </text>
            </g>
          ))}

          {/* Left label column separator */}
          <line
            x1={LEFT_LABEL_WIDTH}
            y1={0}
            x2={LEFT_LABEL_WIDTH}
            y2={totalHeight}
            stroke="var(--color-gray-200)"
            strokeWidth={1}
          />

          {/* Rows */}
          {renderedRows}

          {/* Today marker */}
          {todayOffset >= 0 && todayOffset <= totalDays && (
            <g>
              <line
                x1={LEFT_LABEL_WIDTH + todayOffset * DAY_WIDTH}
                y1={HEADER_HEIGHT}
                x2={LEFT_LABEL_WIDTH + todayOffset * DAY_WIDTH}
                y2={totalHeight}
                stroke="#E53E3E"
                strokeWidth={2}
                strokeDasharray="4,4"
              />
              <text
                x={LEFT_LABEL_WIDTH + todayOffset * DAY_WIDTH + 4}
                y={HEADER_HEIGHT + 14}
                fontSize="10"
                fill="#E53E3E"
                fontWeight="600"
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
