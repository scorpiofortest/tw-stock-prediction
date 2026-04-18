'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCurrency, formatPrice, formatDateTime, formatShares } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { Trade } from '@/types/portfolio'

interface TransactionTableProps {
  trades: Trade[]
  isLoading: boolean
}

export function TransactionTable({ trades, isLoading }: TransactionTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-sm">暫無交易記錄</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>時間</TableHead>
          <TableHead>股票</TableHead>
          <TableHead>方向</TableHead>
          <TableHead className="text-right">數量</TableHead>
          <TableHead className="text-right">價格</TableHead>
          <TableHead className="text-right">手續費</TableHead>
          <TableHead className="text-right">金額</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {trades.map((t) => (
          <TableRow key={t.id}>
            <TableCell className="text-xs text-muted-foreground">
              {formatDateTime(t.traded_at)}
            </TableCell>
            <TableCell>
              <span className="font-mono text-sm">{t.stock_id}</span>
              <span className="ml-1 text-xs text-muted-foreground">{t.stock_name}</span>
            </TableCell>
            <TableCell>
              <Badge variant={t.trade_type === 'buy' ? 'bullish' : 'bearish'}>
                {t.trade_type === 'buy' ? '買入' : '賣出'}
              </Badge>
            </TableCell>
            <TableCell className="text-right font-mono text-sm">
              {formatShares(t.shares)}
            </TableCell>
            <TableCell className="text-right font-mono text-sm">
              {formatPrice(t.price)}
            </TableCell>
            <TableCell className="text-right font-mono text-xs text-muted-foreground">
              {formatCurrency(t.fee + t.tax)}
            </TableCell>
            <TableCell
              className={cn(
                'text-right font-mono text-sm font-medium',
                t.trade_type === 'buy' ? 'text-stock-up' : 'text-stock-down'
              )}
            >
              {t.trade_type === 'buy' ? '-' : '+'}{formatCurrency(Math.abs(t.net_amount))}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
