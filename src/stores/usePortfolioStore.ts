'use client'

import { create } from 'zustand'
import type { Holding, Trade, Account } from '@/types/portfolio'

interface PortfolioStore {
  holdings: Holding[]
  trades: Trade[]
  account: Account | null
  setHoldings: (holdings: Holding[]) => void
  setTrades: (trades: Trade[]) => void
  setAccount: (account: Account) => void
}

export const usePortfolioStore = create<PortfolioStore>((set) => ({
  holdings: [],
  trades: [],
  account: null,
  setHoldings: (holdings) => set({ holdings }),
  setTrades: (trades) => set({ trades }),
  setAccount: (account) => set({ account }),
}))
