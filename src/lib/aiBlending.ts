import type { SignalScore } from '@/types/signal'

export function adaptiveAiWeight(signals: SignalScore[]): number {
  if (!signals || signals.length === 0) return 0.40

  const n = signals.length
  const bullish = signals.filter((s) => s.score > 5).length
  const bearish = signals.filter((s) => s.score < -5).length
  const majority = Math.max(bullish, bearish)
  const agreementRatio = n > 0 ? majority / n : 0.5

  // agreement_ratio ~1.0 (strong consensus) → AI weight 0.30
  // agreement_ratio ~0.5 (50/50 split)      → AI weight 0.55
  const aiWeight = 0.55 - (agreementRatio - 0.5) * 0.50
  return Math.max(0.25, Math.min(0.55, aiWeight))
}

export function inferAiScoreFromText(reasoning: string): number | null {
  if (!reasoning) return null

  const text = reasoning.slice(0, 200)

  // Strong bullish
  if (/強烈看漲|強勢反彈|大幅上漲|顯著看漲/.test(text)) return 50
  // Normal bullish
  if (/走勢看漲|預期.*看漲|判斷.*看漲|方向.*看漲|偏多|反彈向上|帶動.*上/.test(text)) return 30
  // Mild bullish
  if (/微幅看漲|小幅看漲|略偏多/.test(text)) return 15

  // Strong bearish
  if (/強烈看跌|大幅下跌|顯著看跌/.test(text)) return -50
  // Normal bearish
  if (/走勢看跌|預期.*看跌|判斷.*看跌|方向.*看跌|偏空|持續下探/.test(text)) return -30
  // Mild bearish
  if (/微幅看跌|小幅看跌|略偏空/.test(text)) return -15

  // Neutral
  if (/中性|盤整|觀望|方向不明/.test(text)) return 0

  // Last resort: keyword count
  const bullCount = (text.match(/看漲|上漲|反彈|偏多|利多/g) || []).length
  const bearCount = (text.match(/看跌|下跌|回落|偏空|利空/g) || []).length
  if (bullCount > bearCount) return 25
  if (bearCount > bullCount) return -25

  return null
}

function determineDirection(score: number): string {
  if (score > 10) return '看漲'
  if (score < -10) return '看跌'
  return '中性'
}

export function blendScores(
  signalScore: number,
  aiScore: number | null,
  signals: SignalScore[]
): {
  blendedScore: number
  direction: string
  aiWeight: number
} {
  if (aiScore === null) {
    return {
      blendedScore: signalScore,
      direction: determineDirection(signalScore),
      aiWeight: 0,
    }
  }

  const aiW = adaptiveAiWeight(signals)
  const signalW = 1.0 - aiW
  const blendedScore = Math.round((signalScore * signalW + aiScore * aiW) * 100) / 100

  return {
    blendedScore,
    direction: determineDirection(blendedScore),
    aiWeight: Math.round(aiW * 100) / 100,
  }
}
