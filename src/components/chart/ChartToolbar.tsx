'use client'

import { Button } from '@/components/ui/button'
import { TIMEFRAME_OPTIONS } from '@/lib/constants'
import { cn } from '@/lib/utils'
import type { Timeframe } from '@/types/stock'

interface HorizonSelectorProps {
  horizon: Timeframe
  onHorizonChange: (h: Timeframe) => void
  label?: string
}

/**
 * Prediction horizon selector.
 * Chooses the time window that the AI should forecast over.
 */
export function HorizonSelector({ horizon, onHorizonChange, label = '預測區間' }: HorizonSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex items-center gap-1 rounded-md border bg-background p-0.5">
        {TIMEFRAME_OPTIONS.map((option) => (
          <Button
            key={option.value}
            variant={horizon === option.value ? 'default' : 'ghost'}
            size="sm"
            className={cn('h-7 px-2.5 text-xs', horizon === option.value && 'pointer-events-none')}
            onClick={() => onHorizonChange(option.value as Timeframe)}
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
