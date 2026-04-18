'use client'

import { WS_URL } from './constants'

type MessageHandler = (data: unknown) => void
type StatusHandler = (status: 'connecting' | 'connected' | 'disconnected') => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private statusHandlers: Set<StatusHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private isConnecting = false

  constructor(url: string) {
    this.url = url
  }

  get status(): 'connecting' | 'connected' | 'disconnected' {
    if (this.isConnecting) return 'connecting'
    if (this.ws?.readyState === WebSocket.OPEN) return 'connected'
    return 'disconnected'
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) return

    this.isConnecting = true
    this.notifyStatus('connecting')

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.notifyStatus('connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          const handlers = this.handlers.get(message.type)
          if (handlers) {
            handlers.forEach((handler) => handler(message.data || message.payload))
          }
        } catch {
          // ignore parse errors
        }
      }

      this.ws.onclose = (event) => {
        this.isConnecting = false
        this.stopHeartbeat()
        this.notifyStatus('disconnected')
        if (!event.wasClean) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = () => {
        this.isConnecting = false
        this.ws?.close()
      }
    } catch {
      this.isConnecting = false
      this.scheduleReconnect()
    }
  }

  subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)
    return () => {
      this.handlers.get(type)?.delete(handler)
    }
  }

  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler)
    return () => {
      this.statusHandlers.delete(handler)
    }
  }

  send(action: string, data?: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action, ...data }))
    }
  }

  switchStock(oldCode: string | null, newCode: string) {
    if (oldCode) {
      this.send('unsubscribe', { stock_id: oldCode })
    }
    this.send('subscribe', { stock_id: newCode })
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    this.reconnectAttempts++

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  private startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this.send('ping')
    }, 30000)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private notifyStatus(status: 'connecting' | 'connected' | 'disconnected') {
    this.statusHandlers.forEach((handler) => handler(status))
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.stopHeartbeat()
    this.ws?.close()
    this.handlers.clear()
    this.statusHandlers.clear()
  }
}

let wsManager: WebSocketManager | null = null

export function getWSManager(): WebSocketManager {
  if (!wsManager) {
    wsManager = new WebSocketManager(WS_URL)
  }
  return wsManager
}
