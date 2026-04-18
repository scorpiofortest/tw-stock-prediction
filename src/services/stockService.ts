import { api } from './api'
import type { StockSearchResult, StockQuote, KlineRaw, Kline } from '@/types/stock'

// Valid yfinance periods accepted by backend
const VALID_PERIODS = new Set(['1d', '5d', '1mo', '3mo', '6mo', '1y'])

export const stockService = {
  search: (query: string) =>
    api.get<StockSearchResult[]>('/stocks/search', { q: query }),

  getQuote: (code: string) =>
    api.get<StockQuote>(`/stocks/${code}/quote`),

  getHistory: async (code: string, period: string = '3mo'): Promise<Kline[]> => {
    const p = VALID_PERIODS.has(period) ? period : '3mo'
    const raw = await api.get<KlineRaw[]>(`/stocks/${code}/history`, { period: p })
    return raw.map((k) => ({
      time: k.date,
      open: k.open,
      high: k.high,
      low: k.low,
      close: k.close,
      volume: k.volume,
    }))
  },
}
