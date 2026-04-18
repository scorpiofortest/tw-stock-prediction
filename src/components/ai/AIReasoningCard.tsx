'use client'

import { Bot, Activity, Newspaper, BarChart2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AIToggle } from './AIToggle'
import { AILoadingState } from './AILoadingState'
import { TypewriterText } from './TypewriterText'
import { useSettingsStore } from '@/stores/useSettingsStore'
import { formatDateTime } from '@/lib/formatters'

interface AIReasoningCardProps {
  reasoning?: string | null
  isLoading: boolean
  timestamp?: string
  model?: string
  sources?: {
    signals: boolean
    fundamentals: boolean
    news_count: number
  }
}

export function AIReasoningCard({
  reasoning,
  isLoading,
  timestamp,
  model,
  sources,
}: AIReasoningCardProps) {
  const { aiEnabled: isAiEnabled } = useSettingsStore()

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Bot className="h-5 w-5 text-blue-500" />
          AI 智慧推論
          {model && (
            <span className="rounded bg-blue-500/10 px-1.5 py-0.5 font-mono text-[10px] text-blue-500">
              {model}
            </span>
          )}
        </CardTitle>
        <AIToggle />
      </CardHeader>
      <CardContent>
        {!isAiEnabled ? (
          <p className="text-sm text-muted-foreground">
            AI 推論已關閉，僅顯示訊號評分結果。
          </p>
        ) : isLoading ? (
          <AILoadingState />
        ) : reasoning ? (
          <div className="space-y-3">
            <div className="rounded-lg bg-muted/50 p-4">
              <p className="whitespace-pre-line text-sm leading-relaxed">
                <TypewriterText text={reasoning} speed={20} />
              </p>
            </div>

            {/* Source badges */}
            {sources && (
              <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                <span className="text-muted-foreground">依據：</span>
                {sources.signals && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5">
                    <Activity className="h-3 w-3" />
                    15 大分析訊號
                  </span>
                )}
                {sources.fundamentals && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5">
                    <BarChart2 className="h-3 w-3" />
                    基本面
                  </span>
                )}
                {sources.news_count > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5">
                    <Newspaper className="h-3 w-3" />
                    {sources.news_count} 則新聞
                  </span>
                )}
              </div>
            )}

            {timestamp && (
              <p className="text-xs text-muted-foreground">
                {formatDateTime(timestamp)}
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            選擇股票後將自動產生 AI 推論分析。
          </p>
        )}
      </CardContent>
    </Card>
  )
}
