/**
 * WebSocket Types (FE-DASH-002)
 *
 * Types for WebSocket communication with the dashboard API.
 * These types mirror the Pydantic schemas from src/api/websocket/events.py
 */

// ============================================================================
// WebSocket Event Types
// ============================================================================

export type WebSocketEventType =
  | 'bot_status'
  | 'position_update'
  | 'order_update'
  | 'price_update'
  | 'activity_event'
  | 'heartbeat'
  | 'error'
  | 'connection_established'
  | 'pong'
  | 'subscription_confirmed'

// ============================================================================
// Event Data Types
// ============================================================================

export interface BotStatusEventData {
  state: 'WAIT' | 'ACTIVATE' | 'ACTIVE' | 'PAUSE' | 'INACTIVE'
  is_running: boolean
  macd_trend: 'bullish' | 'bearish' | 'neutral' | null
  grid_active: boolean
  pending_orders_count: number
  filled_orders_count: number
}

export interface PositionUpdateEventData {
  symbol: string
  side: 'LONG' | 'SHORT'
  size: string
  entry_price: string
  current_price: string
  unrealized_pnl: string
  leverage: number
  timestamp: string
}

export interface OrderUpdateEventData {
  order_id: string
  symbol: string
  side: 'BUY' | 'SELL'
  order_type: 'LIMIT' | 'MARKET'
  status: 'NEW' | 'FILLED' | 'CANCELLED' | 'PARTIALLY_FILLED'
  price: string
  quantity: string
  filled_quantity: string
  timestamp: string
}

export interface PriceUpdateEventData {
  symbol: string
  price: string
  change_24h: string | null
  change_percent_24h: string | null
  timestamp: string
}

export interface ActivityEventData {
  event_type: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'success'
  metadata: Record<string, unknown> | null
  timestamp: string
}

export interface HeartbeatEventData {
  timestamp: string
  server_time: string
}

export interface ErrorEventData {
  code: string
  message: string
  timestamp: string
}

export interface ConnectionEstablishedData {
  message: string
  user: string
}

export interface SubscriptionConfirmedData {
  events: string[]
}

// ============================================================================
// WebSocket Event Wrapper
// ============================================================================

export interface WebSocketEvent<T = unknown> {
  type: WebSocketEventType
  data: T
  timestamp: string
}

// Type guards for event types
export type BotStatusEvent = WebSocketEvent<BotStatusEventData>
export type PositionUpdateEvent = WebSocketEvent<PositionUpdateEventData>
export type OrderUpdateEvent = WebSocketEvent<OrderUpdateEventData>
export type PriceUpdateEvent = WebSocketEvent<PriceUpdateEventData>
export type ActivityEvent = WebSocketEvent<ActivityEventData>
export type HeartbeatEvent = WebSocketEvent<HeartbeatEventData>
export type ErrorEvent = WebSocketEvent<ErrorEventData>

// ============================================================================
// Client Message Types
// ============================================================================

export interface PingMessage {
  type: 'ping'
}

export interface SubscribeMessage {
  type: 'subscribe'
  events: WebSocketEventType[]
}

export interface RequestStatusMessage {
  type: 'request_status'
}

export type ClientMessage = PingMessage | SubscribeMessage | RequestStatusMessage

// ============================================================================
// Connection State Types
// ============================================================================

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

export interface WebSocketState {
  connectionState: ConnectionState
  lastHeartbeat: Date | null
  reconnectAttempts: number
  error: string | null
}
