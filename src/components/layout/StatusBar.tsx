'use client'

import { Wifi, WifiOff, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatusBarProps {
  wsStatus: 'connecting' | 'connected' | 'disconnected'
  lastUpdated?: string
}

export function StatusBar({ wsStatus, lastUpdated }: StatusBarProps) {
  return (
    <div className="hidden h-8 items-center justify-between border-t bg-muted/30 px-4 text-xs text-muted-foreground lg:flex">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          {wsStatus === 'connected' ? (
            <Wifi className="h-3 w-3 text-green-500" />
          ) : (
            <WifiOff className="h-3 w-3 text-red-500" />
          )}
          <span
            className={cn(
              wsStatus === 'connected' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}
          >
            {wsStatus === 'connected' ? '即時連線' : wsStatus === 'connecting' ? '連線中...' : '離線'}
          </span>
        </div>

        {lastUpdated && (
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>最後更新: {lastUpdated}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span>v1.0.0</span>
        <span>|</span>
        <span>僅供實驗研究</span>
      </div>
    </div>
  )
}
