'use client'

import { Skeleton } from '@/components/ui/skeleton'

export function AILoadingState() {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 animate-bounce rounded-full bg-blue-500" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:0.2s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:0.4s]" />
        <span className="text-sm text-muted-foreground">AI 正在分析中...</span>
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-4 w-3/5" />
    </div>
  )
}
