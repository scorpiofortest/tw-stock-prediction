'use client'

import { Switch } from '@/components/ui/switch'
import { useSettingsStore } from '@/stores/useSettingsStore'
import { cn } from '@/lib/utils'

export function AIToggle() {
  const { aiEnabled: isAiEnabled, toggleAi } = useSettingsStore()

  return (
    <div className="flex items-center gap-2">
      <Switch
        checked={isAiEnabled}
        onCheckedChange={toggleAi}
        className={cn(
          isAiEnabled && 'bg-gradient-to-r from-blue-500 to-purple-500'
        )}
      />
      <span className="text-sm">
        {isAiEnabled ? (
          <span className="bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text font-medium text-transparent">
            AI 已啟用
          </span>
        ) : (
          <span className="text-muted-foreground">AI 已關閉</span>
        )}
      </span>
    </div>
  )
}
