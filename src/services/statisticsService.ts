import { api } from './api'
import type { DashboardStats } from '@/types/api'
import type { SignalAccuracyData } from '@/types/signal'

export const statisticsService = {
  getDashboard: () =>
    api.get<DashboardStats>('/stats/dashboard'),

  getSignalAccuracy: () =>
    api.get<SignalAccuracyData[]>('/stats/signals/accuracy'),
}
