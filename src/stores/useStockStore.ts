'use client'

import { create } from 'zustand'
import type { CompositeScore } from '@/types/signal'

interface StockStore {
  currentStock: string | null
  prediction: CompositeScore | null
  signals: any[]
  aiReasoning: string | null
  isAiEnabled: boolean
  setCurrentStock: (code: string | null) => void
  setPrediction: (result: CompositeScore | null) => void
  setSignals: (signals: any[]) => void
  setAiReasoning: (reasoning: string | null) => void
  toggleAi: () => void
  setAiEnabled: (enabled: boolean) => void
}

export const useStockStore = create<StockStore>((set) => ({
  currentStock: null,
  prediction: null,
  signals: [],
  aiReasoning: null,
  isAiEnabled: true,
  setCurrentStock: (code) => set({ currentStock: code }),
  setPrediction: (result) => set({ prediction: result }),
  setSignals: (signals) => set({ signals }),
  setAiReasoning: (reasoning) => set({ aiReasoning: reasoning }),
  toggleAi: () => set((state) => ({ isAiEnabled: !state.isAiEnabled })),
  setAiEnabled: (enabled) => set({ isAiEnabled: enabled }),
}))
