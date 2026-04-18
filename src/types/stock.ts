export interface Stock {
  code: string
  name: string
  market: 'twse' | 'tpex'
}

export interface StockQuote {
  stock_id: string
  stock_name: string
  current_price: number
  change: number
  change_percent: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  updated_at: string
}

export interface KlineRaw {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Kline {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// Prediction horizon: how far into the future we're forecasting
export type Timeframe = '1d' | '3d' | '1w' | '2w' | '1mo'

export interface StockSearchResult {
  stock_id: string
  stock_name: string
  market: string
}
