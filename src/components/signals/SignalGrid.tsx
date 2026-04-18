'use client'

import { SignalCard } from './SignalCard'
import { Skeleton } from '@/components/ui/skeleton'
import type { SignalScore } from '@/types/signal'

interface SignalGridProps {
  signals: SignalScore[]
  isLoading: boolean
}

export function SignalGrid({ signals, isLoading }: SignalGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 15 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-6">
            <Skeleton className="mb-2 h-4 w-24" />
            <Skeleton className="mb-3 h-8 w-16" />
            <Skeleton className="mb-2 h-2 w-full" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {signals.map((signal) => (
        <SignalCard key={signal.name} signal={signal} />
      ))}
    </div>
  )
}
