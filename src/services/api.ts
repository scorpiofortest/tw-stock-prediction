import { API_BASE_URL } from '@/lib/constants'
import type { ApiResponse } from '@/types/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string
  ) {
    super(`API Error ${status}: ${body}`)
    this.name = 'ApiError'
  }
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`)
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          url.searchParams.set(k, v)
        }
      })
    }
    const res = await fetch(url.toString(), {
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) throw new ApiError(res.status, await res.text())
    const json: ApiResponse<T> = await res.json()
    return json.data
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) throw new ApiError(res.status, await res.text())
    const json: ApiResponse<T> = await res.json()
    return json.data
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) throw new ApiError(res.status, await res.text())
    const json: ApiResponse<T> = await res.json()
    return json.data
  }
}

export const api = new ApiClient(API_BASE_URL)
