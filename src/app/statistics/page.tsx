'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AccuracyChart } from '@/components/statistics/AccuracyChart'
import { PredictionHistory } from '@/components/statistics/PredictionHistory'
import { SignalAccuracy } from '@/components/statistics/SignalAccuracy'
import { TrendLineChart } from '@/components/statistics/TrendLineChart'
import { usePredictionStats, usePredictionHistory } from '@/hooks/usePrediction'
import { useQuery } from '@tanstack/react-query'
import { statisticsService } from '@/services/statisticsService'

export default function StatisticsPage() {
  const [page, setPage] = useState(1)

  const { data: stats, isLoading: statsLoading } = usePredictionStats()
  const { data: historyData, isLoading: historyLoading } = usePredictionHistory({
    page: page.toString(),
    pageSize: '20',
  })
  const { data: signalAccuracy, isLoading: signalLoading } = useQuery({
    queryKey: ['signalAccuracy'],
    queryFn: () => statisticsService.getSignalAccuracy(),
    staleTime: 60000,
  })

  // Mock trend data - in production this would come from the API
  const trendData = Array.from({ length: 30 }, (_, i) => ({
    date: `04/${String(i + 1).padStart(2, '0')}`,
    value: 50 + Math.random() * 30,
  }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">歷史統計</h1>

      {/* Top Row: Accuracy + Signal Accuracy */}
      <div className="grid gap-6 lg:grid-cols-2">
        <AccuracyChart
          successRate={stats?.success_rate || 0}
          totalPredictions={stats?.total_predictions || 0}
          successCount={stats?.success_count || 0}
          isLoading={statsLoading}
        />

        <SignalAccuracy
          data={signalAccuracy || []}
          isLoading={signalLoading}
        />
      </div>

      {/* Trend Line */}
      <TrendLineChart
        data={trendData}
        title="成功率趨勢"
        color="#3b82f6"
      />

      {/* Prediction History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">預測記錄</CardTitle>
        </CardHeader>
        <CardContent>
          <PredictionHistory
            records={historyData?.items || []}
            isLoading={historyLoading}
          />

          {historyData && historyData.totalPages > 1 && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <button
                className="rounded border px-3 py-1 text-sm disabled:opacity-50"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                上一頁
              </button>
              <span className="text-sm text-muted-foreground">
                {page} / {historyData.totalPages}
              </span>
              <button
                className="rounded border px-3 py-1 text-sm disabled:opacity-50"
                disabled={page >= historyData.totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                下一頁
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
