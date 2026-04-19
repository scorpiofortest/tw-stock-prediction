'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIStore {
  theme: 'light' | 'dark' | 'system'
  sidebarOpen: boolean
  mobileSidebarOpen: boolean
  activeTab: string
  favoriteStocks: string[]
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setMobileSidebarOpen: (open: boolean) => void
  toggleMobileSidebar: () => void
  setActiveTab: (tab: string) => void
  addFavorite: (code: string) => void
  removeFavorite: (code: string) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      theme: 'system',
      sidebarOpen: true,
      mobileSidebarOpen: false,
      activeTab: 'dashboard',
      favoriteStocks: ['2330', '2317', '2454', '0050'],
      setTheme: (theme) => set({ theme }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
      toggleMobileSidebar: () => set((state) => ({ mobileSidebarOpen: !state.mobileSidebarOpen })),
      setActiveTab: (tab) => set({ activeTab: tab }),
      addFavorite: (code) =>
        set((state) => ({
          favoriteStocks: state.favoriteStocks.includes(code)
            ? state.favoriteStocks
            : [...state.favoriteStocks, code],
        })),
      removeFavorite: (code) =>
        set((state) => ({
          favoriteStocks: state.favoriteStocks.filter((c) => c !== code),
        })),
    }),
    { name: 'tw-stock-ui' }
  )
)
