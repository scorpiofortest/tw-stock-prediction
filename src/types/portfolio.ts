export interface Holding {
  stock_id: string
  stock_name: string
  shares: number
  avg_cost: number
  current_price: number
  total_cost: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
}

export interface Trade {
  id: string
  stock_id: string
  stock_name: string
  trade_type: 'buy' | 'sell'
  shares: number
  price: number
  amount: number
  fee: number
  tax: number
  net_amount: number
  realized_pnl?: number
  traded_at: string
}

export interface Account {
  username: string
  initial_capital: number
  current_cash: number
  total_stock_value: number
  total_assets: number
  total_pnl: number
  total_pnl_pct: number
  positions_count: number
}

export interface TradeRequest {
  stock_id: string
  shares: number
  price: number
}

export interface TradeResult {
  success: boolean
  trade: Trade
  account: Account
}
