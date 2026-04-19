export interface SignalScore {
  name: string
  value: number
  score: number
  weight: number
  weighted_score: number
  description: string
  reliability: number
}

export interface CompositeScoreData {
  total_score: number
  signal_score?: number
  ai_score?: number | null
  direction: string
  confidence: number
  signal_agreement: string
  calculated_at: string
}

export interface AIAnalysis {
  available: boolean
  reasoning: string
  ai_score?: number | null
  message?: string
  horizon?: string
  model?: string
  from_cache?: boolean
  sources?: {
    signals: boolean
    fundamentals: boolean
    news_count: number
  }
}

export interface Fundamentals {
  pe: number
  forward_pe: number
  pb: number
  eps: number
  dividend_yield: number
  market_cap: number
  week_52_high: number
  week_52_low: number
  beta: number
  sector: string
  industry: string
  has_dividend?: boolean
  last_dividend_amount?: number
  last_dividend_date?: string
  dividend_frequency?: number
  dividend_months?: number[]
}

export interface NewsItem {
  title: string
  source: string
  published: string
  link: string
}

export interface CompositeScore {
  stock_id: string
  stock_name: string
  current_price: number
  change_pct: number
  horizon?: string
  horizon_label?: string
  composite_score: CompositeScoreData
  signals: SignalScore[]
  fundamentals?: Fundamentals
  news?: NewsItem[]
  ai_analysis: AIAnalysis
}

export interface SignalAccuracyData {
  signalName: string
  accuracy: number
  totalCount: number
  correctCount: number
}
