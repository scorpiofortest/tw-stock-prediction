'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCurrency, formatPrice, formatPercent, formatShares } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { Holding } from '@/types/portfolio'

interface HoldingsTableProps {
  holdings: Holding[]
  isLoading: boolean
  onSell?: (holding: Holding) => void
}

export function HoldingsTable({ holdings, isLoading, onSell }: HoldingsTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (holdings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-sm">目前沒有持倉</p>
        <p className="text-xs">搜尋股票並買入開始模擬交易</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>股票</TableHead>
          <TableHead className="text-right">持有</TableHead>
          <TableHead className="text-right">平均成本</TableHead>
          <TableHead className="text-right">現價</TableHead>
          <TableHead className="text-right">損益</TableHead>
          <TableHead className="text-right">損益%</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {holdings.map((h) => (
          <TableRow key={h.stock_id}>
            <TableCell>
              <div className="flex flex-col">
                <span className="font-mono font-medium">{h.stock_id}</span>
                <span className="text-xs text-muted-foreground">{h.stock_name}</span>
              </div>
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatShares(h.shares)}
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatPrice(h.avg_cost)}
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatPrice(h.current_price)}
            </TableCell>
            <TableCell
              className={cn(
                'text-right font-mono font-medium',
                h.unrealized_pnl > 0 ? 'text-stock-up' : h.unrealized_pnl < 0 ? 'text-stock-down' : ''
              )}
            >
              {formatCurrency(h.unrealized_pnl)}
            </TableCell>
            <TableCell className="text-right">
              <Badge variant={h.unrealized_pnl_pct > 0 ? 'bullish' : h.unrealized_pnl_pct < 0 ? 'bearish' : 'secondary'}>
                {formatPercent(h.unrealized_pnl_pct)}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              <Button
                variant="bearish"
                size="sm"
                onClick={() => onSell?.(h)}
              >
                賣出
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
