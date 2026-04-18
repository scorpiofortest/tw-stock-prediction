'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { TransactionTable } from '@/components/portfolio/TransactionTable'
import { useTrades } from '@/hooks/usePortfolio'

export default function TradeHistoryPage() {
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const { data, isLoading } = useTrades({
    page: page.toString(),
    page_size: '20',
    trade_type: typeFilter === 'all' ? undefined : typeFilter,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/portfolio">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <h1 className="text-2xl font-bold">交易歷史</h1>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">交易記錄</CardTitle>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="類型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="buy">買入</SelectItem>
              <SelectItem value="sell">賣出</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          <TransactionTable
            trades={data || []}
            isLoading={isLoading}
          />

          {data && data.length >= 20 && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                上一頁
              </Button>
              <span className="text-sm text-muted-foreground">
                第 {page} 頁
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={(data?.length || 0) < 20}
                onClick={() => setPage((p) => p + 1)}
              >
                下一頁
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
