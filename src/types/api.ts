export interface ApiResponse<T> {
  success: boolean
  data: T
  timestamp: string
}

export interface ApiError {
  success: false
  error: string
  code: number
  timestamp: string
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface DashboardStats {
  totalPredictions: number
  successRate: number
  todayPredictions: number
  todaySuccessRate: number
  totalAssets: number
  totalPnl: number
  rolling20: number
  rolling50: number
  rolling100: number
}
