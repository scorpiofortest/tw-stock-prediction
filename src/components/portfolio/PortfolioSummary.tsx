'use client'

import { DollarSign, TrendingUp, Wallet, PiggyBank } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCurrency, formatPercent } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { Account } from '@/types/portfolio'

interface PortfolioSummaryProps {
  account: Account | null
  isLoading: boolean
}

const cards = [
  {
    title: '總資產',
    icon: DollarSign,
    key: 'total_assets' as const,
    format: formatCurrency,
  },
  {
    title: '持倉市值',
    icon: TrendingUp,
    key: 'total_stock_value' as const,
    format: formatCurrency,
  },
  {
    title: '可用現金',
    icon: Wallet,
    key: 'current_cash' as const,
    format: formatCurrency,
  },
  {
    title: '總損益',
    icon: PiggyBank,
    key: 'total_pnl' as const,
    format: formatCurrency,
    showPercent: true,
  },
]

export function PortfolioSummary({ account, isLoading }: PortfolioSummaryProps) {
  if (isLoading || !account) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.key}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => {
        const value = account[c.key]
        const isPnl = c.key === 'total_pnl'
        return (
          <Card key={c.key}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {c.title}
              </CardTitle>
              <c.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div
                className={cn(
                  'text-2xl font-bold font-mono',
                  isPnl && value > 0 && 'text-stock-up',
                  isPnl && value < 0 && 'text-stock-down'
                )}
              >
                {c.format(value)}
              </div>
              {c.showPercent && (
                <p
                  className={cn(
                    'mt-1 text-xs font-mono',
                    account.total_pnl_pct > 0 ? 'text-stock-up' : account.total_pnl_pct < 0 ? 'text-stock-down' : 'text-muted-foreground'
                  )}
                >
                  {formatPercent(account.total_pnl_pct)}
                </p>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
