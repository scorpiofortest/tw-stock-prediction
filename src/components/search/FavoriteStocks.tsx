'use client'

import Link from 'next/link'
import { Star, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/stores/useUIStore'
import { cn } from '@/lib/utils'

export function FavoriteStocks() {
  const { favoriteStocks, removeFavorite } = useUIStore()

  return (
    <div className="space-y-1">
      <h4 className="px-2 text-xs font-semibold text-muted-foreground">常用股票</h4>
      {favoriteStocks.map((code) => (
        <div key={code} className="group flex items-center gap-1">
          <Link
            href={`/stock/${code}`}
            className="flex flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-accent"
          >
            <span className="font-mono">{code}</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100"
            onClick={() => removeFavorite(code)}
          >
            <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
          </Button>
        </div>
      ))}
    </div>
  )
}
