'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'
import {
  CommandDialog, CommandInput, CommandList, CommandEmpty,
  CommandGroup, CommandItem, CommandSeparator,
} from '@/components/ui/command'
import { useStockSearch } from '@/hooks/useStockData'
import { useDebounce } from '@/hooks/useDebounce'
import { useStockStore } from '@/stores/useStockStore'
import { formatPrice, formatPercent } from '@/lib/formatters'
import { cn } from '@/lib/utils'

export function StockSearch() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const debouncedQuery = useDebounce(query, 300)
  const { data: results } = useStockSearch(debouncedQuery)
  const { setCurrentStock } = useStockStore()
  const router = useRouter()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  const handleSelect = useCallback(
    (code: string) => {
      setCurrentStock(code)
      setOpen(false)
      setQuery('')
      router.push(`/stock/${code}`)
    },
    [setCurrentStock, router]
  )

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex h-9 w-full items-center gap-2 rounded-lg border bg-background px-3 text-sm text-muted-foreground transition-colors hover:bg-accent md:max-w-md"
      >
        <Search className="h-4 w-4" />
        <span>搜尋股票代碼或名稱...</span>
        <kbd className="ml-auto hidden rounded border bg-muted px-1.5 text-xs font-mono sm:inline-block">
          ⌘K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          placeholder="輸入股票代碼或名稱..."
          value={query}
          onValueChange={setQuery}
        />
        <CommandList>
          <CommandEmpty>找不到相關股票</CommandEmpty>

          {results && results.length > 0 && (
            <CommandGroup heading="搜尋結果">
              {results.map((stock) => (
                <CommandItem
                  key={stock.stock_id}
                  value={`${stock.stock_id} ${stock.stock_name}`}
                  onSelect={() => handleSelect(stock.stock_id)}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium">{stock.stock_id}</span>
                    <span className="text-sm">{stock.stock_name}</span>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {!query && (
            <CommandGroup heading="熱門股票">
              {[
                { code: '2330', name: '台積電' },
                { code: '2317', name: '鴻海' },
                { code: '2454', name: '聯發科' },
                { code: '0050', name: '元大台灣50' },
              ].map((stock) => (
                <CommandItem
                  key={stock.code}
                  value={`${stock.code} ${stock.name}`}
                  onSelect={() => handleSelect(stock.code)}
                >
                  <span className="font-mono font-medium">{stock.code}</span>
                  <span className="ml-2 text-sm">{stock.name}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}
        </CommandList>
      </CommandDialog>
    </>
  )
}
