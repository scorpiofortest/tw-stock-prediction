'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { portfolioService } from '@/services/portfolioService'
import type { TradeRequest } from '@/types/portfolio'

export function useAccount() {
  return useQuery({
    queryKey: ['account'],
    queryFn: () => portfolioService.getAccount(),
    staleTime: 10000,
  })
}

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: () => portfolioService.getPositions(),
    staleTime: 10000,
  })
}

export function useBuy() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: TradeRequest) => portfolioService.buy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['trades'] })
    },
  })
}

export function useSell() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: TradeRequest) => portfolioService.sell(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['trades'] })
    },
  })
}

export function useTrades(params?: {
  page?: string
  page_size?: string
  stock_id?: string
  trade_type?: string
}) {
  return useQuery({
    queryKey: ['trades', params],
    queryFn: () => portfolioService.getTrades(params),
    staleTime: 10000,
  })
}

export function useResetPortfolio() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (initialCapital?: number) => portfolioService.reset(initialCapital),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
      queryClient.invalidateQueries({ queryKey: ['positions'] })
      queryClient.invalidateQueries({ queryKey: ['trades'] })
    },
  })
}
