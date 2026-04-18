'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfidenceRing } from '@/components/prediction/ConfidenceRing'
import { Skeleton } from '@/components/ui/skeleton'

interface AccuracyChartProps {
  successRate: number
  totalPredictions: number
  successCount: number
  isLoading: boolean
}

export function AccuracyChart({ successRate, totalPredictions, successCount, isLoading }: AccuracyChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-24" />
        </CardHeader>
        <CardContent className="flex flex-col items-center">
          <Skeleton className="h-32 w-32 rounded-full" />
          <Skeleton className="mt-4 h-4 w-32" />
        </CardContent>
      </Card>
    )
  }

  const direction = successRate >= 65 ? 'bullish' : successRate >= 50 ? 'neutral' : 'bearish'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">整體成功率</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-3">
        <ConfidenceRing value={Math.round(successRate)} direction={direction} size={140} />
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            {successCount} / {totalPredictions} 筆正確
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
