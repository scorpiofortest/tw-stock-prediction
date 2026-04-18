'use client'

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { DIRECTION_LABELS } from '@/lib/constants'
import type { Direction } from '@/types/prediction'

const directionIcons = {
  bullish: TrendingUp,
  bearish: TrendingDown,
  neutral: Minus,
}

const variantMap = {
  bullish: 'bullish',
  bearish: 'bearish',
  neutral: 'neutral',
} as const

interface PredictionBadgeProps {
  direction: Direction
  confidence?: number
}

export function PredictionBadge({ direction, confidence }: PredictionBadgeProps) {
  const Icon = directionIcons[direction]
  const label = DIRECTION_LABELS[direction]

  return (
    <Badge variant={variantMap[direction]} className="gap-1">
      <Icon className="h-3 w-3" />
      <span>{label}</span>
      {confidence !== undefined && <span className="ml-0.5 opacity-80">{confidence}%</span>}
    </Badge>
  )
}
