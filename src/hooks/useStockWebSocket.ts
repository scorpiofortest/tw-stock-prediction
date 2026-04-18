'use client'

import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getWSManager } from '@/lib/websocket'
import { useStockStore } from '@/stores/useStockStore'

export function useStockWebSocket(stockCode: string | null) {
  const queryClient = useQueryClient()
  const { setPrediction, setSignals } = useStockStore()
  const prevCode = useRef<string | null>(null)
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')

  useEffect(() => {
    if (!stockCode) return

    const ws = getWSManager()
    ws.connect()
    ws.switchStock(prevCode.current, stockCode)
    prevCode.current = stockCode

    const unsubStatus = ws.onStatusChange(setStatus)

    const unsubQuote = ws.subscribe('quote_update', (data) => {
      queryClient.setQueryData(['stockQuote', stockCode], data)
    })

    const unsubSignal = ws.subscribe('signal_update', (data) => {
      const d = data as { signals: typeof useStockStore extends never ? never : Parameters<typeof setSignals>[0] }
      if (d.signals) {
        queryClient.setQueryData(['signals', stockCode], d.signals)
        setSignals(d.signals as never)
      }
    })

    const unsubPrediction = ws.subscribe('prediction_created', (data) => {
      queryClient.setQueryData(['prediction', stockCode], data)
      setPrediction(data as never)
    })

    const unsubVerify = ws.subscribe('prediction_verified', (data) => {
      queryClient.invalidateQueries({ queryKey: ['predictions'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      void data
    })

    return () => {
      unsubStatus()
      unsubQuote()
      unsubSignal()
      unsubPrediction()
      unsubVerify()
    }
  }, [stockCode, queryClient, setPrediction, setSignals])

  return { status }
}
