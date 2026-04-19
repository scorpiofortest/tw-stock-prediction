'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Clock, CheckCircle2, XCircle, AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { formatDate, formatPrice, formatPercent, formatTimeAgo } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { PredictionRecord } from '@/types/prediction'

interface PredictionHistoryProps {
  records: PredictionRecord[]
  isLoading: boolean
}

const directionMap: Record<string, { label: string; icon: typeof TrendingUp; variant: string }> = {
  up: { label: '看漲', icon: TrendingUp, variant: 'bullish' },
  down: { label: '看跌', icon: TrendingDown, variant: 'bearish' },
  flat: { label: '中性', icon: Minus, variant: 'secondary' },
}

export function PredictionHistory({ records, isLoading }: PredictionHistoryProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (records.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-sm">暫無預測記錄</p>
        <p className="mt-1 text-xs">在儀表板或個股頁面點擊「建立預測紀錄」</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>建立時間</TableHead>
          <TableHead>股票</TableHead>
          <TableHead>預測方向</TableHead>
          <TableHead>區間</TableHead>
          <TableHead className="text-right">信心值</TableHead>
          <TableHead className="text-right">建立時股價</TableHead>
          <TableHead className="text-right">驗證時股價</TableHead>
          <TableHead className="text-right">漲跌幅</TableHead>
          <TableHead className="text-center">狀態</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {records.map((r) => {
          const dir = directionMap[r.predicted_direction] || directionMap.flat
          const DirIcon = dir.icon

          return (
            <TableRow key={r.id}>
              <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                {r.predicted_at ? formatDate(r.predicted_at, 'MM/dd HH:mm') : '-'}
              </TableCell>
              <TableCell>
                <span className="font-mono text-sm">{r.stock_id}</span>
                <span className="ml-1 text-xs text-muted-foreground">{r.stock_name}</span>
              </TableCell>
              <TableCell>
                <Badge variant={dir.variant as any} className="gap-1">
                  <DirIcon className="h-3 w-3" />
                  {dir.label}
                </Badge>
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {r.horizon_label || r.horizon || '-'}
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {(r.predicted_confidence ?? 0).toFixed(0)}%
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {formatPrice(r.price_at_prediction)}
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {r.price_at_verify != null ? formatPrice(r.price_at_verify) : '-'}
              </TableCell>
              <TableCell
                className={cn(
                  'text-right font-mono text-sm',
                  r.price_change_pct != null && r.price_change_pct > 0
                    ? 'text-stock-up'
                    : r.price_change_pct != null && r.price_change_pct < 0
                    ? 'text-stock-down'
                    : ''
                )}
              >
                {r.price_change_pct != null ? formatPercent(r.price_change_pct) : '-'}
              </TableCell>
              <TableCell className="text-center">
                <StatusBadge record={r} />
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

function StatusBadge({ record }: { record: PredictionRecord }) {
  if (record.status === 'pending') {
    const timeLeft = record.verify_after
      ? formatTimeAgo(record.verify_after)
      : ''
    return (
      <Badge variant="secondary" className="gap-1">
        <Clock className="h-3 w-3" />
        <span>等待驗證</span>
        {timeLeft && (
          <span className="ml-0.5 text-[10px] opacity-70">{timeLeft}</span>
        )}
      </Badge>
    )
  }

  if (record.status === 'expired') {
    return (
      <Badge variant="outline" className="gap-1 text-muted-foreground">
        <AlertCircle className="h-3 w-3" />
        已過期
      </Badge>
    )
  }

  // verified
  if (record.is_correct === true) {
    return (
      <Badge className="gap-1 bg-green-600 text-white hover:bg-green-600">
        <CheckCircle2 className="h-3 w-3" />
        預測正確
      </Badge>
    )
  }
  if (record.is_correct === false) {
    return (
      <Badge variant="destructive" className="gap-1">
        <XCircle className="h-3 w-3" />
        預測錯誤
      </Badge>
    )
  }

  // is_correct === null → flat, not counted
  return (
    <Badge variant="outline" className="gap-1">
      <Minus className="h-3 w-3" />
      平盤不計
    </Badge>
  )
}
