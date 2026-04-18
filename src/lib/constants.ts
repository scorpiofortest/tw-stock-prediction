export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

export const SIGNAL_NAMES: Record<string, string> = {
  outer_ratio: '外盤比率',
  bid_ask_pressure: '五檔委買委賣壓力',
  tick_direction: '最近10筆成交方向',
  intraday_position: '日內高低位置',
  momentum: '即時漲跌幅動能',
  rsi: 'RSI 指標',
  macd: 'MACD OSC',
  kd: 'KD 指標',
  acceleration: '盤中走勢加速度',
  institutional_flow: '籌碼面',
  volume_price: '量價結構',
  market_correlation: '大盤連動',
  moving_average: '均線系統',
  volatility: '波動率',
  time_factor: '時間因子',
}

export const SIGNAL_WEIGHTS: Record<string, number> = {
  outer_ratio: 0.08,
  bid_ask_pressure: 0.07,
  tick_direction: 0.06,
  intraday_position: 0.05,
  momentum: 0.06,
  rsi: 0.07,
  macd: 0.07,
  kd: 0.06,
  acceleration: 0.03,
  institutional_flow: 0.15,
  volume_price: 0.08,
  market_correlation: 0.08,
  moving_average: 0.07,
  volatility: 0.04,
  time_factor: 0.03,
}

export const SIGNAL_ICONS: Record<string, string> = {
  outer_ratio: 'BarChart3',
  bid_ask_pressure: 'Scale',
  tick_direction: 'ArrowUpDown',
  intraday_position: 'TrendingUp',
  momentum: 'Zap',
  rsi: 'Activity',
  macd: 'LineChart',
  kd: 'GitBranch',
  acceleration: 'Gauge',
  institutional_flow: 'Users',
  volume_price: 'BarChart',
  market_correlation: 'Globe',
  moving_average: 'Waves',
  volatility: 'AlertTriangle',
  time_factor: 'Clock',
}

export const DIRECTION_COLORS = {
  bullish: {
    text: 'text-stock-up',
    bg: 'bg-stock-up-bg',
    border: 'border-stock-up',
    fill: '#ef4444',
  },
  bearish: {
    text: 'text-stock-down',
    bg: 'bg-stock-down-bg',
    border: 'border-stock-down',
    fill: '#22c55e',
  },
  neutral: {
    text: 'text-stock-flat',
    bg: 'bg-stock-flat-bg',
    border: 'border-stock-flat',
    fill: '#eab308',
  },
} as const

export const DIRECTION_LABELS = {
  bullish: '看漲',
  bearish: '看跌',
  neutral: '中性',
} as const

export const DIRECTION_ARROWS = {
  bullish: '▲',
  bearish: '▼',
  neutral: '─',
} as const

// Prediction horizon options: how far into the future the AI forecasts
export const TIMEFRAME_OPTIONS = [
  { label: '1日', value: '1d' },
  { label: '3日', value: '3d' },
  { label: '1週', value: '1w' },
  { label: '2週', value: '2w' },
  { label: '1個月', value: '1mo' },
] as const

export const HORIZON_LABELS: Record<string, string> = {
  '1d': '1日',
  '3d': '3日',
  '1w': '1週',
  '2w': '2週',
  '1mo': '1個月',
}

export const NAV_ITEMS = [
  { label: '儀表板', href: '/dashboard', icon: 'LayoutDashboard' },
  { label: '模擬倉', href: '/portfolio', icon: 'Briefcase' },
  { label: '歷史統計', href: '/statistics', icon: 'BarChart2' },
  { label: '設定', href: '/settings', icon: 'Settings' },
] as const

export const INITIAL_CAPITAL = 10000000
export const FEE_RATE = 0.001425
export const FEE_DISCOUNT = 0.6
export const MIN_FEE = 20
export const TAX_RATE = 0.003
