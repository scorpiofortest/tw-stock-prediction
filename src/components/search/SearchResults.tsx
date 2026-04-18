'use client'

import { formatPrice, formatPercent } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { StockSearchResult } from '@/types/stock'

interface SearchResultsProps {
  results: StockSearchResult[]
  onSelect: (code: string) => void
}

export function SearchResults({ results, onSelect }: SearchResultsProps) {
  if (results.length === 0) {
    return <p className="px-4 py-6 text-center text-sm text-muted-foreground">找不到相關股票</p>
  }

  return (
    <div className="divide-y">
      {results.map((stock) => (
        <button
          key={stock.stock_id}
          onClick={() => onSelect(stock.stock_id)}
          className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-accent"
        >
          <div>
            <span className="font-mono font-medium">{stock.stock_id}</span>
            <span className="ml-2 text-sm">{stock.stock_name}</span>
            <span className="ml-2 text-xs text-muted-foreground">{stock.market}</span>
          </div>
        </button>
      ))}
    </div>
  )
}
