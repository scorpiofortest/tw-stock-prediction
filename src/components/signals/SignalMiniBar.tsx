'use client'

import { DIRECTION_COLORS } from '@/lib/constants'
import type { Direction } from '@/types/prediction'

interface SignalMiniBarProps {
  data: number[]
  direction: Direction
  height?: number
}

export function SignalMiniBar({ data, direction, height = 24 }: SignalMiniBarProps) {
  if (data.length === 0) return null

  const max = Math.max(...data.map(Math.abs), 1)
  const barWidth = 100 / data.length
  const fillColor = DIRECTION_COLORS[direction].fill

  return (
    <svg width="100%" height={height} className="overflow-hidden rounded">
      {data.map((value, i) => {
        const barHeight = (Math.abs(value) / max) * height
        const y = value >= 0 ? height / 2 - barHeight : height / 2
        return (
          <rect
            key={i}
            x={`${i * barWidth}%`}
            y={value >= 0 ? height / 2 - barHeight : height / 2}
            width={`${barWidth * 0.8}%`}
            height={barHeight}
            fill={fillColor}
            opacity={0.6 + (i / data.length) * 0.4}
            rx={1}
          />
        )
      })}
      <line
        x1="0"
        y1={height / 2}
        x2="100%"
        y2={height / 2}
        stroke="hsl(var(--border))"
        strokeWidth={0.5}
      />
    </svg>
  )
}
