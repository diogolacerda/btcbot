/**
 * Dashboard WebSocket Hook (FE-DASH-002)
 *
 * React hook for real-time WebSocket connection to the dashboard API.
 * Handles JWT authentication, event subscriptions, auto-reconnect,
 * and TanStack Query cache updates.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { dashboardKeys } from './useDashboardData'
import type {
  WebSocketEvent,
  BotStatusEventData,
  PositionUpdateEventData,
  OrderUpdateEventData,
  PriceUpdateEventData,
  ActivityEventData,
  ConnectionState,
  ClientMessage,
} from '../types/websocket'

// ============================================================================
// Configuration
// ============================================================================

const WS_URL = '__VITE_API_URL__'.replace(/^http/, 'ws')
const WS_PATH = '/ws/dashboard'

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000] // Exponential backoff capped at 30s
const MAX_RECONNECT_ATTEMPTS = 10
const PING_INTERVAL = 25000 // 25 seconds (server heartbeat is 30s)

// ============================================================================
// Types
// ============================================================================

export interface UseDashboardWebSocketOptions {
  enabled?: boolean
  onBotStatus?: (data: BotStatusEventData) => void
  onPositionUpdate?: (data: PositionUpdateEventData) => void
  onOrderUpdate?: (data: OrderUpdateEventData) => void
  onPriceUpdate?: (data: PriceUpdateEventData) => void
  onActivityEvent?: (data: ActivityEventData) => void
  onError?: (error: string) => void
  onConnectionChange?: (state: ConnectionState) => void
}

export interface UseDashboardWebSocketReturn {
  connectionState: ConnectionState
  lastHeartbeat: Date | null
  reconnectAttempts: number
  error: string | null
  connect: () => void
  disconnect: () => void
  sendMessage: (message: ClientMessage) => void
  requestStatus: () => void
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useDashboardWebSocket(
  options: UseDashboardWebSocketOptions = {}
): UseDashboardWebSocketReturn {
  const {
    enabled = true,
    onBotStatus,
    onPositionUpdate,
    onOrderUpdate,
    onPriceUpdate,
    onActivityEvent,
    onError,
    onConnectionChange,
  } = options

  // State
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const shouldReconnectRef = useRef(true)
  const reconnectAttemptsRef = useRef(0) // Ref for use in callbacks
  const connectRef = useRef<(() => void) | undefined>(undefined) // Ref to break circular dependency

  // Query client for cache updates
  const queryClient = useQueryClient()

  // ============================================================================
  // Connection State Updates
  // ============================================================================

  const updateConnectionState = useCallback(
    (state: ConnectionState) => {
      setConnectionState(state)
      onConnectionChange?.(state)
    },
    [onConnectionChange]
  )

  // ============================================================================
  // Cache Invalidation Helpers
  // ============================================================================

  const invalidateBotStatus = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: dashboardKeys.botStatus() })
  }, [queryClient])

  const invalidateOrders = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: dashboardKeys.orders() })
    queryClient.invalidateQueries({ queryKey: dashboardKeys.positions() })
  }, [queryClient])

  const invalidateMarketData = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: dashboardKeys.price() })
  }, [queryClient])

  const invalidateActivity = useCallback(() => {
    // Invalidate all activity queries
    queryClient.invalidateQueries({
      predicate: (query) => {
        const key = query.queryKey
        return Array.isArray(key) && key[0] === 'dashboard' && key[1] === 'activity'
      },
    })
  }, [queryClient])

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const wsEvent: WebSocketEvent = JSON.parse(event.data)

        switch (wsEvent.type) {
          case 'bot_status':
            onBotStatus?.(wsEvent.data as BotStatusEventData)
            invalidateBotStatus()
            break

          case 'position_update':
            onPositionUpdate?.(wsEvent.data as PositionUpdateEventData)
            invalidateOrders()
            break

          case 'order_update':
            onOrderUpdate?.(wsEvent.data as OrderUpdateEventData)
            invalidateOrders()
            break

          case 'price_update':
            onPriceUpdate?.(wsEvent.data as PriceUpdateEventData)
            invalidateMarketData()
            break

          case 'activity_event':
            onActivityEvent?.(wsEvent.data as ActivityEventData)
            invalidateActivity()
            break

          case 'heartbeat':
            setLastHeartbeat(new Date())
            break

          case 'pong':
            setLastHeartbeat(new Date())
            break

          case 'connection_established':
            reconnectAttemptsRef.current = 0
            setReconnectAttempts(0)
            setError(null)
            break

          case 'error': {
            const errorData = wsEvent.data as { code: string; message: string }
            setError(errorData.message)
            onError?.(errorData.message)
            break
          }

          case 'subscription_confirmed':
            // Subscription acknowledged
            break

          default:
            // Unknown event type - log for debugging
            console.warn('[WebSocket] Unknown event type:', wsEvent.type)
        }
      } catch (err) {
        console.error('[WebSocket] Failed to parse message:', err)
      }
    },
    [
      onBotStatus,
      onPositionUpdate,
      onOrderUpdate,
      onPriceUpdate,
      onActivityEvent,
      onError,
      invalidateBotStatus,
      invalidateOrders,
      invalidateMarketData,
      invalidateActivity,
    ]
  )

  // ============================================================================
  // Ping/Pong Keep-Alive
  // ============================================================================

  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }

    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, PING_INTERVAL)
  }, [])

  const stopPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }, [])

  // ============================================================================
  // Reconnection Logic (Exponential Backoff)
  // ============================================================================

  const scheduleReconnect = useCallback(() => {
    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    // Check if we should still reconnect
    if (!shouldReconnectRef.current) {
      return
    }

    // Check max attempts
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      setError(`Failed to reconnect after ${MAX_RECONNECT_ATTEMPTS} attempts`)
      onError?.(`Failed to reconnect after ${MAX_RECONNECT_ATTEMPTS} attempts`)
      updateConnectionState('disconnected')
      return
    }

    // Calculate delay using exponential backoff (capped at last value in array)
    const delayIndex = Math.min(reconnectAttemptsRef.current, RECONNECT_DELAYS.length - 1)
    const delay = RECONNECT_DELAYS[delayIndex]

    // Increment attempts
    reconnectAttemptsRef.current += 1
    setReconnectAttempts(reconnectAttemptsRef.current)

    console.log(
      `[WebSocket] Scheduling reconnect attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS} in ${delay}ms`
    )

    // Schedule reconnection
    reconnectTimeoutRef.current = setTimeout(() => {
      if (shouldReconnectRef.current) {
        connectRef.current?.()
      }
    }, delay)
  }, [onError, updateConnectionState])

  // ============================================================================
  // Connection Management
  // ============================================================================

  const connect = useCallback(() => {
    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token')

    if (!token) {
      setError('No authentication token available')
      onError?.('No authentication token available')
      return
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    shouldReconnectRef.current = true
    updateConnectionState('connecting')

    // Build WebSocket URL with token
    const wsUrl = `${WS_URL}${WS_PATH}?token=${encodeURIComponent(token)}`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        updateConnectionState('connected')
        setError(null)
        startPingInterval()

        // Subscribe to all events
        ws.send(
          JSON.stringify({
            type: 'subscribe',
            events: ['bot_status', 'position_update', 'order_update', 'price_update', 'activity_event'],
          })
        )
      }

      ws.onmessage = handleMessage

      ws.onerror = () => {
        setError('WebSocket connection error')
        onError?.('WebSocket connection error')
      }

      ws.onclose = (event) => {
        stopPingInterval()
        updateConnectionState('disconnected')

        // Handle authentication failure
        if (event.code === 1008) {
          setError('Authentication failed')
          onError?.('Authentication failed')
          shouldReconnectRef.current = false
          return
        }

        // Auto-reconnect if enabled and not intentionally disconnected
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          updateConnectionState('reconnecting')
          scheduleReconnect()
        }
      }

      wsRef.current = ws
    } catch {
      setError('Failed to create WebSocket connection')
      onError?.('Failed to create WebSocket connection')
    }
  }, [
    updateConnectionState,
    handleMessage,
    startPingInterval,
    stopPingInterval,
    scheduleReconnect,
    onError,
  ])

  // Update ref to break circular dependency
  connectRef.current = connect

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    stopPingInterval()

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    updateConnectionState('disconnected')
    reconnectAttemptsRef.current = 0
    setReconnectAttempts(0)
  }, [stopPingInterval, updateConnectionState])

  // ============================================================================
  // Message Sending
  // ============================================================================

  const sendMessage = useCallback((message: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('[WebSocket] Cannot send message: connection not open')
    }
  }, [])

  const requestStatus = useCallback(() => {
    sendMessage({ type: 'request_status' })
  }, [sendMessage])

  // ============================================================================
  // Effect: Auto-connect on mount
  // ============================================================================

  useEffect(() => {
    if (enabled) {
      connect()
    }

    return () => {
      disconnect()
    }
    // Only run on mount/unmount and when enabled changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled])

  return {
    connectionState,
    lastHeartbeat,
    reconnectAttempts,
    error,
    connect,
    disconnect,
    sendMessage,
    requestStatus,
  }
}

export default useDashboardWebSocket
