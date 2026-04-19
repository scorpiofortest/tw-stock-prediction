'use client'

import { BarChart2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Fundamentals } from '@/types/signal'

interface FundamentalsCardProps {
  data?: Fundamentals
}

function formatMarketCap(value: number): string {
  if (!value) return '—'
  if (value >= 1e12) return `${(value / 1e12).toFixed(2)} 兆`
  if (value >= 1e8) return `${(value / 1e8).toFixed(2)} 億`
  return value.toLocaleString()
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between py-1 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium">{value}</span>
    </div>
  )
}

export function FundamentalsCard({ data }: FundamentalsCardProps) {
  const isEmpty = !data || Object.keys(data).length === 0 ||
    (!data.pe && !data.pb && !data.eps && !data.dividend_yield && !data.market_cap && !data.beta && !data.sector)
  if (isEmpty) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart2 className="h-5 w-5 text-emerald-500" />
            基本面快照
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">暫無基本面資料</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart2 className="h-5 w-5 text-emerald-500" />
          基本面快照
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-0.5">
        {(data.pe ?? 0) > 0 && <Row label="本益比 PE" value={data.pe!.toFixed(2)} />}
        {(data.forward_pe ?? 0) > 0 && <Row label="預估 PE" value={data.forward_pe!.toFixed(2)} />}
        {(data.pb ?? 0) > 0 && <Row label="股價淨值比 PB" value={data.pb!.toFixed(2)} />}
        {data.eps != null && data.eps !== 0 && <Row label="EPS(TTM)" value={data.eps.toFixed(2)} />}
        {(data.dividend_yield ?? 0) > 0 && (
          <Row label="殖利率" value={`${data.dividend_yield!.toFixed(2)}%`} />
        )}
        {(data.market_cap ?? 0) > 0 && (
          <Row label="市值" value={formatMarketCap(data.market_cap!)} />
        )}
        {(data.week_52_high ?? 0) > 0 && (data.week_52_low ?? 0) > 0 && (
          <Row
            label="52 週區間"
            value={`${data.week_52_low} ~ ${data.week_52_high}`}
          />
        )}
        {(data.beta ?? 0) > 0 && <Row label="Beta" value={data.beta!.toFixed(2)} />}
        {data.sector && (
          <Row
            label="產業"
            value={data.industry ? `${data.sector} · ${data.industry}` : data.sector}
          />
        )}

        {/* 配息資訊 */}
        {data.has_dividend != null && (
          <>
            <div className="border-t my-2" />
            <Row label="是否配息" value={data.has_dividend ? '是' : '否'} />
          </>
        )}
        {data.has_dividend && data.last_dividend_date && (
          <Row
            label="上次配息"
            value={`${data.last_dividend_amount ?? 0} 元 (${data.last_dividend_date})`}
          />
        )}
        {data.has_dividend && data.dividend_months && data.dividend_months.length > 0 && (
          <Row
            label="配息月份"
            value={data.dividend_months.map((m) => `${m}月`).join('、')}
          />
        )}
        {data.has_dividend && (data.dividend_frequency ?? 0) > 0 && (
          <Row
            label="配息頻率"
            value={
              data.dividend_frequency === 1
                ? '年配'
                : data.dividend_frequency === 2
                ? '半年配'
                : data.dividend_frequency === 4
                ? '季配'
                : `每年 ${data.dividend_frequency} 次`
            }
          />
        )}
      </CardContent>
    </Card>
  )
}
