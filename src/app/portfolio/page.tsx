'use client'

import { useState } from 'react'
import Link from 'next/link'
import { History } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { PortfolioSummary } from '@/components/portfolio/PortfolioSummary'
import { HoldingsTable } from '@/components/portfolio/HoldingsTable'
import { AssetPieChart } from '@/components/portfolio/AssetPieChart'
import { TransactionTable } from '@/components/portfolio/TransactionTable'
import { TradePanel } from '@/components/portfolio/TradePanel'
import { useAccount, usePositions, useTrades } from '@/hooks/usePortfolio'
import type { Holding } from '@/types/portfolio'

export default function PortfolioPage() {
  const { data: account, isLoading: accountLoading } = useAccount()
  const { data: positions, isLoading: positionsLoading } = usePositions()
  const { data: tradesData, isLoading: tradesLoading } = useTrades({ page_size: '10' })
  const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">模擬倉</h1>
        <Button variant="outline" asChild>
          <Link href="/portfolio/history">
            <History className="mr-2 h-4 w-4" />
            交易歷史
          </Link>
        </Button>
      </div>

      {/* Summary Cards */}
      <PortfolioSummary account={account || null} isLoading={accountLoading} />

      {/* Holdings Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">持倉列表</CardTitle>
        </CardHeader>
        <CardContent>
          <HoldingsTable
            holdings={positions || []}
            isLoading={positionsLoading}
            onSell={(h) => setSelectedHolding(h)}
          />
        </CardContent>
      </Card>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {positions && positions.length > 0 && account && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">資產配置</CardTitle>
            </CardHeader>
            <CardContent>
              <AssetPieChart holdings={positions} cash={account.current_cash} />
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">近期交易</CardTitle>
            <Button variant="link" size="sm" asChild>
              <Link href="/portfolio/history">查看全部</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <TransactionTable
              trades={tradesData || []}
              isLoading={tradesLoading}
            />
          </CardContent>
        </Card>
      </div>

      <p className="text-center text-xs text-muted-foreground">
        模擬交易不涉及真實資金，僅供練習使用。
      </p>

      {/* Sell Dialog */}
      <Dialog
        open={selectedHolding !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedHolding(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              賣出 {selectedHolding?.stock_id} {selectedHolding?.stock_name}
            </DialogTitle>
          </DialogHeader>
          {selectedHolding && account && (
            <TradePanel
              stockCode={selectedHolding.stock_id}
              stockName={selectedHolding.stock_name}
              currentPrice={selectedHolding.current_price}
              cash={account.current_cash}
              maxSellShares={selectedHolding.shares}
              initialTab="sell"
              hideBuyTab
              borderless
              onSuccess={() => setSelectedHolding(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
