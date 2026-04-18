'use client'

import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { SIGNAL_NAMES, DIRECTION_COLORS } from '@/lib/constants'
import type { SignalScore } from '@/types/signal'
import type { Direction } from '@/types/prediction'

interface SignalRadarChartProps {
  signals: SignalScore[]
  direction: Direction
}

export function SignalRadarChart({ signals, direction }: SignalRadarChartProps) {
  const option = useMemo(() => {
    const indicator = signals.map((s) => ({
      name: s.name,
      max: 100,
    }))

    const values = signals.map((s) => Math.abs(s.score))
    const fillColor = DIRECTION_COLORS[direction].fill

    return {
      radar: {
        indicator,
        shape: 'polygon',
        splitNumber: 4,
        axisName: {
          color: 'hsl(var(--muted-foreground))',
          fontSize: 11,
        },
        splitLine: {
          lineStyle: {
            color: 'hsl(var(--border))',
          },
        },
        splitArea: {
          show: false,
        },
        axisLine: {
          lineStyle: {
            color: 'hsl(var(--border))',
          },
        },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: values,
              name: '訊號強度',
              areaStyle: {
                color: `${fillColor}33`,
              },
              lineStyle: {
                color: fillColor,
                width: 2,
              },
              itemStyle: {
                color: fillColor,
              },
            },
          ],
          animationDuration: 1500,
        },
      ],
      tooltip: {
        trigger: 'item',
      },
    }
  }, [signals, direction])

  return (
    <ReactECharts
      option={option}
      style={{ height: '100%', minHeight: 300 }}
      opts={{ renderer: 'canvas' }}
    />
  )
}
