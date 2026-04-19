'use client'

import { useEffect, useState } from 'react'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { MobileNav } from '@/components/layout/MobileNav'
import { StatusBar } from '@/components/layout/StatusBar'
import { useTheme } from '@/hooks/useTheme'
import { getWSManager } from '@/lib/websocket'

export function AppShell({ children }: { children: React.ReactNode }) {
  // Initialize theme
  useTheme()

  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')

  useEffect(() => {
    const ws = getWSManager()
    const unsub = ws.onStatusChange(setWsStatus)
    return unsub
  }, [])

  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pb-14 lg:pb-0">
          <div className="mx-auto max-w-7xl p-4 lg:p-6">{children}</div>
        </main>
      </div>
      <StatusBar wsStatus={wsStatus} />
      <MobileNav />
    </div>
  )
}
