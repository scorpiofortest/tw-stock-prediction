export type Direction = 'bullish' | 'bearish' | 'neutral'

export type DirectionLabel = '強烈看漲' | '看漲' | '微幅看漲' | '中性' | '微幅看跌' | '看跌' | '強烈看跌'

export interface PredictionResult {
  stockCode: string
  stockName: string
  timestamp: string
  currentPrice: number
  changePct: number
  weightedTotalScore: number
  direction: Direction
  directionLabel: DirectionLabel
  confidence: number
  signalAgreement: string
  aiReasoning?: string
}

export interface PredictionRecord {
  id: number
  stock_id: string
  stock_name: string
  predicted_at: string
  predicted_direction: string  // 'up' | 'down' | 'flat'
  predicted_confidence: number
  price_at_prediction: number
  signal_score?: number
  ai_involved: boolean
  horizon: string
  horizon_label: string
  verify_after?: string
  verify_at?: string
  price_at_verify?: number
  actual_direction?: string
  price_change_pct?: number
  status: 'pending' | 'verified' | 'expired'
  is_correct?: boolean | null
}

export interface VerificationResult {
  analysisTimestamp: string
  verifyTimestamp: string
  predictedDirection: Direction
  priceAtPrediction: number
  priceAtVerify: number
  changePct: number
  result: 'success' | 'fail' | 'flat'
}
