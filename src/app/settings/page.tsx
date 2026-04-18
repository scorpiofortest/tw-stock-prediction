'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { useSettingsStore } from '@/stores/useSettingsStore'
import { useTheme } from '@/hooks/useTheme'
import { useAccount, useResetPortfolio } from '@/hooks/usePortfolio'

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const {
    geminiApiKey, geminiModel, aiEnabled,
    setGeminiApiKey, setGeminiModel, setAiEnabled,
  } = useSettingsStore()
  const { data: account } = useAccount()
  const resetMutation = useResetPortfolio()

  const [showResetDialog, setShowResetDialog] = useState(false)
  const [showApplyDialog, setShowApplyDialog] = useState(false)
  const [capitalInput, setCapitalInput] = useState<string>('')

  // Local input state for API key (don't show stored key directly)
  const [keyInput, setKeyInput] = useState('')
  const [modelInput, setModelInput] = useState(geminiModel)
  const [showApiKey, setShowApiKey] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  useEffect(() => {
    setModelInput(geminiModel)
  }, [geminiModel])

  // Sync input with backend value when account loads
  useEffect(() => {
    if (account?.initial_capital != null) {
      setCapitalInput(String(Math.round(account.initial_capital)))
    }
  }, [account?.initial_capital])

  const parsedCapital = parseInt(capitalInput.replace(/[,\s]/g, ''), 10)
  const isValidCapital = !isNaN(parsedCapital) && parsedCapital > 0
  const isCapitalChanged = isValidCapital && account?.initial_capital !== parsedCapital

  const handleReset = () => {
    resetMutation.mutate(undefined)
    setShowResetDialog(false)
  }

  const handleApplyCapital = () => {
    if (!isValidCapital) return
    resetMutation.mutate(parsedCapital)
    setShowApplyDialog(false)
  }

  const handleSaveAiSettings = () => {
    if (keyInput.trim()) {
      setGeminiApiKey(keyInput.trim())
    }
    if (modelInput.trim()) {
      setGeminiModel(modelInput.trim())
    }
    setKeyInput('')
    setSaveMsg('已儲存')
    setTimeout(() => setSaveMsg(null), 2000)
  }

  // Mask the stored key for display
  const maskedKey = geminiApiKey
    ? geminiApiKey.length > 8
      ? geminiApiKey.slice(0, 4) + '*'.repeat(geminiApiKey.length - 8) + geminiApiKey.slice(-4)
      : '****'
    : ''

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">設定</h1>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">一般設定</CardTitle>
          <CardDescription>調整應用外觀與行為</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">主題</p>
              <p className="text-xs text-muted-foreground">選擇深色或淺色模式</p>
            </div>
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
              className="h-9 w-36 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="light">淺色模式</option>
              <option value="dark">深色模式</option>
              <option value="system">跟隨系統</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* AI Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">AI 設定</CardTitle>
          <CardDescription>
            管理 AI 推論功能。支援 Google Gemini 系列模型（如 gemini-2.5-flash、gemini-2.5-pro 等）。
            需填入 Google AI Studio 的 API Key。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">AI 推論</p>
              <p className="text-xs text-muted-foreground">啟用 AI 生成分析說明</p>
            </div>
            <Switch checked={aiEnabled} onCheckedChange={setAiEnabled} />
          </div>

          <Separator />

          {/* API Key */}
          <div className="space-y-2">
            <div>
              <p className="text-sm font-medium">Google API Key</p>
              <p className="text-xs text-muted-foreground">
                從{' '}
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline text-primary"
                >
                  Google AI Studio
                </a>
                {' '}取得 API Key
              </p>
            </div>
            {maskedKey && !keyInput && (
              <p className="text-xs font-mono text-muted-foreground">目前: {maskedKey}</p>
            )}
            <div className="flex items-center gap-2">
              <Input
                type={showApiKey ? 'text' : 'password'}
                placeholder="輸入新的 API Key（留空則不更動）"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                className="h-9 font-mono text-sm"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="shrink-0 text-xs w-12"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? '隱藏' : '顯示'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              API Key 僅儲存在您的瀏覽器中，不會傳送至任何伺服器
            </p>
          </div>

          <Separator />

          {/* Model */}
          <div className="space-y-2">
            <div>
              <p className="text-sm font-medium">主要模型</p>
              <p className="text-xs text-muted-foreground">
                用於 AI 分析的主要模型名稱
              </p>
            </div>
            <Input
              type="text"
              value={modelInput}
              onChange={(e) => setModelInput(e.target.value)}
              placeholder="例如 gemini-2.5-flash"
              className="h-9 font-mono text-sm"
            />
          </div>

          {/* Save */}
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              onClick={handleSaveAiSettings}
            >
              儲存 AI 設定
            </Button>
            {saveMsg && (
              <span className="text-xs text-green-500">
                {saveMsg}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Portfolio Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">模擬倉設定</CardTitle>
          <CardDescription>調整模擬交易參數</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium">初始資金</p>
              <p className="text-xs text-muted-foreground">
                模擬倉起始金額（套用後會重置持倉與交易記錄）
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">NT$</span>
              <Input
                type="number"
                min={1}
                step={10000}
                value={capitalInput}
                onChange={(e) => setCapitalInput(e.target.value)}
                className="h-9 w-40 text-right font-mono"
              />
              <Button
                size="sm"
                disabled={!isCapitalChanged || resetMutation.isPending}
                onClick={() => setShowApplyDialog(true)}
              >
                套用
              </Button>
            </div>
          </div>
          {isValidCapital && (
            <p className="-mt-3 text-right text-xs font-mono text-muted-foreground">
              = NT$ {parsedCapital.toLocaleString('en-US')}
            </p>
          )}

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">手續費率</p>
              <p className="text-xs text-muted-foreground">0.1425% x 6折</p>
            </div>
            <span className="font-mono text-sm">0.0855%</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">證交稅</p>
              <p className="text-xs text-muted-foreground">賣出時收取</p>
            </div>
            <span className="font-mono text-sm">0.3%</span>
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-destructive">重置模擬倉</p>
              <p className="text-xs text-muted-foreground">清除所有持倉與交易記錄</p>
            </div>
            <Button variant="destructive" size="sm" onClick={() => setShowResetDialog(true)}>
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">關於</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>台股實驗預測及模擬倉 v1.0.0</p>
          <p>本系統僅供學術研究與技術實驗使用，所有分析結果不構成投資建議。</p>
          <p>股市有風險，投資需謹慎。</p>
        </CardContent>
      </Card>

      {/* Reset Dialog */}
      <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>確認重置模擬倉</DialogTitle>
            <DialogDescription>
              此操作將清除所有持倉、交易記錄，並將現金重置為初始資金 NT${' '}
              {(account?.initial_capital || 0).toLocaleString('en-US')}。此操作無法復原。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResetDialog(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleReset} disabled={resetMutation.isPending}>
              {resetMutation.isPending ? '處理中...' : '確認重置'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Apply New Capital Dialog */}
      <Dialog open={showApplyDialog} onOpenChange={setShowApplyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>套用新的初始資金</DialogTitle>
            <DialogDescription>
              <span className="block">
                將初始資金從 NT$ {(account?.initial_capital || 0).toLocaleString('en-US')} 調整為{' '}
                <span className="font-mono font-semibold text-foreground">
                  NT$ {isValidCapital ? parsedCapital.toLocaleString('en-US') : '-'}
                </span>
                。
              </span>
              <span className="mt-2 block text-destructive">
                此操作會清除目前所有持倉、交易記錄與資產快照，無法復原。
              </span>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApplyDialog(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleApplyCapital}
              disabled={!isValidCapital || resetMutation.isPending}
            >
              {resetMutation.isPending ? '處理中...' : '確認套用'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
