import { api } from './api'
import type { Account, Holding, Trade, TradeRequest, TradeResult } from '@/types/portfolio'

export const portfolioService = {
  getAccount: () =>
    api.get<Account>('/portfolio/account'),

  getPositions: () =>
    api.get<Holding[]>('/portfolio/positions'),

  buy: (data: TradeRequest) =>
    api.post<TradeResult>('/portfolio/buy', data),

  sell: (data: TradeRequest) =>
    api.post<TradeResult>('/portfolio/sell', data),

  getTrades: (params?: {
    page?: string
    page_size?: string
    stock_id?: string
    trade_type?: string
  }) =>
    api.get<Trade[]>('/portfolio/trades', params),

  reset: (initialCapital?: number) =>
    api.post<Account>(
      '/portfolio/reset',
      initialCapital ? { initial_capital: initialCapital } : {}
    ),
}
