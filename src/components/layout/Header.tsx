'use client'

import { Menu, Moon, Sun, Settings, Monitor, BotOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/stores/useUIStore'
import { useTheme } from '@/hooks/useTheme'
import { useSettingsStore } from '@/stores/useSettingsStore'
import { StockSearch } from '@/components/search/StockSearch'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function Header() {
  const { toggleMobileSidebar } = useUIStore()
  const { theme, setTheme } = useTheme()
  const { aiEnabled } = useSettingsStore()
  const hasKey = useSettingsStore((s) => s.geminiApiKey.trim().length > 0)

  const aiUnavailable = !hasKey || !aiEnabled

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:px-6">
      <Button variant="ghost" size="icon" onClick={toggleMobileSidebar} className="lg:hidden">
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex items-center gap-2">
        <div className="hidden items-center gap-2 font-semibold lg:flex">
          <span className="text-lg">台股預測</span>
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">實驗版</span>
        </div>
      </div>

      <div className="flex-1 px-4">
        <StockSearch />
      </div>

      <div className="flex items-center gap-2">
        {aiUnavailable && (
          <a
            href="/settings"
            title={!hasKey ? '尚未設定 API Key，請至設定頁面配置' : 'AI 推論已關閉'}
            className="flex items-center gap-1.5 rounded-full border border-yellow-500/30 bg-yellow-500/10 px-3 py-1.5 text-xs font-medium text-yellow-600 transition-colors hover:bg-yellow-500/20 dark:text-yellow-400"
          >
            <BotOff className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">AI 未啟用</span>
          </a>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              {theme === 'dark' ? (
                <Moon className="h-5 w-5" />
              ) : theme === 'light' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Monitor className="h-5 w-5" />
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme('light')}>
              <Sun className="mr-2 h-4 w-4" />
              淺色
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('dark')}>
              <Moon className="mr-2 h-4 w-4" />
              深色
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('system')}>
              <Monitor className="mr-2 h-4 w-4" />
              跟隨系統
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="ghost" size="icon" asChild>
          <a href="/settings">
            <Settings className="h-5 w-5" />
          </a>
        </Button>
      </div>
    </header>
  )
}
