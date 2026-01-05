// API Request/Response Types
// These types correspond to Pydantic schemas in the backend API
// They use camelCase and will be transformed to snake_case when sent to the API

import type { Position, Trade, TradeStats } from './index'

// ============================================================================
// Authentication API Types
// ============================================================================

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name?: string | null
}

export interface TokenResponse {
  accessToken: string
  tokenType: string
}

export interface UserResponse {
  id: string
  email: string
  name: string | null
  isActive: boolean
}

// ============================================================================
// Trading Data API Types
// ============================================================================

export interface PositionsListResponse {
  positions: Position[]
  total: number
}

export interface TradesListResponse {
  trades: Trade[]
  total: number
  limit: number
  offset: number
}

export type TradeStatsResponse = TradeStats

// ============================================================================
// Config API Types
// ============================================================================

export interface TradingConfigRequest {
  symbol?: string
  leverage?: number
  orderSizeUsdt?: number
  marginMode?: 'CROSSED' | 'ISOLATED'
  takeProfitPercent?: number
}

export interface TradingConfigResponse {
  id: string
  accountId: string
  symbol: string
  leverage: number
  orderSizeUsdt: number
  marginMode: 'CROSSED' | 'ISOLATED'
  takeProfitPercent: number
  createdAt: string
  updatedAt: string
}

export interface GridConfigRequest {
  gridSpacing?: number
  maxTotalOrders?: number
  gridAnchorMode?: 'none' | 'hundred'
}

export interface GridConfigResponse {
  id: string
  accountId: string
  gridSpacing: number
  maxTotalOrders: number
  gridAnchorMode: 'none' | 'hundred'
  createdAt: string
  updatedAt: string
}

export interface DynamicTPConfigRequest {
  enabled?: boolean
  baseTP?: number
  minTP?: number
  maxTP?: number
  safetyMargin?: number
  checkInterval?: number
}

export interface DynamicTPConfigResponse {
  id: string
  accountId: string
  enabled: boolean
  baseTP: number
  minTP: number
  maxTP: number
  safetyMargin: number
  checkInterval: number
  createdAt: string
  updatedAt: string
}

// ============================================================================
// Filter API Types
// ============================================================================

export interface MACDFilterStatusResponse {
  enabled: boolean
  currentState: 'ALLOW' | 'BLOCK'
  trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | null
  lastUpdate: string | null
  macdValue: number | null
  signalValue: number | null
  histogram: number | null
}

export interface MACDFilterToggleRequest {
  enabled: boolean
}

// ============================================================================
// Health/Status API Types
// ============================================================================

export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  version: string
  timestamp: string
  uptime: number
  botState?: string
  activeFilters?: string[]
}

// ============================================================================
// Dashboard API Types (FE-DASH-001)
// ============================================================================

// Bot Control Types
export interface MACDValues {
  macdLine: number
  histogram: number
}

export interface OrderStats {
  pendingOrders: number
  openPositions: number
  totalTrades: number
  totalPnl: number
}

export interface ErrorStatus {
  marginError: boolean
  rateLimited: boolean
}

export interface BotStatusResponse {
  status: 'running' | 'stopped' | 'paused'
  state: 'INACTIVE' | 'WAIT' | 'ACTIVATE' | 'ACTIVE' | 'PAUSE'
  stateDescription: string
  isRunning: boolean
  cycleActivated: boolean
  cycleActivatedAt: string | null
  lastUpdate: string
  currentPrice: number
  macd: MACDValues
  orders: OrderStats
  errors: ErrorStatus
}

// Market Data Types
export type MACDSignal = 'bullish' | 'bearish' | 'neutral'

export interface PriceResponse {
  symbol: string
  price: number
  change24h: number
  change24hPercent: number
  high24h: number
  low24h: number
  volume24h: number
  timestamp: string
}

export interface FundingRateResponse {
  symbol: string
  fundingRate: number
  fundingRatePercent: number
  nextFundingTime: string
  fundingIntervalHours: number
  markPrice: number
  timestamp: string
}

export interface MACDDataResponse {
  symbol: string
  macdLine: number
  signalLine: number
  histogram: number
  signal: MACDSignal
  histogramRising: boolean
  bothLinesNegative: boolean
  timeframe: string
  timestamp: string
}

export interface GridRangeResponse {
  symbol: string
  currentPrice: number
  gridLow: number
  gridHigh: number
  rangePercent: number
  pricePositionPercent: number
  levelsPossible: number
  timestamp: string
}

// Performance Metrics Types
export type TimePeriod = 'today' | '7days' | '30days' | 'custom'

export interface PeriodMetrics {
  period: string
  startDate: string
  endDate: string
  realizedPnl: number
  pnlPercent: number
  tradesClosed: number
  winningTrades: number
  losingTrades: number
  winRate: number
}

export interface TotalMetrics {
  totalPnl: number
  totalTrades: number
  avgProfitPerTrade: number
  totalFees: number
  netPnl: number
  bestTrade: number
  worstTrade: number
}

export interface PerformanceMetricsResponse {
  periodMetrics: PeriodMetrics
  totalMetrics: TotalMetrics
}

// Orders Types
export type OrderStatusEnum = 'PENDING' | 'FILLED' | 'TP_HIT' | 'CANCELLED'

export interface OrderSchema {
  orderId: string
  price: number
  tpPrice: number
  quantity: number
  side: 'LONG' | 'SHORT'
  status: OrderStatusEnum
  createdAt: string
  filledAt: string | null
  closedAt: string | null
  exchangeTpOrderId: string | null
}

export interface OrdersListResponse {
  orders: OrderSchema[]
  total: number
  limit: number
  offset: number
  pendingCount: number
  filledCount: number
}

// Activity Events Types
export type EventTypeEnum =
  | 'ORDER_FILLED'
  | 'TRADE_CLOSED'
  | 'STRATEGY_PAUSED'
  | 'STRATEGY_RESUMED'
  | 'TP_ADJUSTED'
  | 'CYCLE_ACTIVATED'
  | 'CYCLE_DEACTIVATED'
  | 'BOT_STARTED'
  | 'BOT_STOPPED'
  | 'ERROR_OCCURRED'

export interface ActivityEventSchema {
  id: string
  eventType: EventTypeEnum
  description: string
  eventData: Record<string, unknown> | null
  timestamp: string
}

export interface ActivityEventsListResponse {
  events: ActivityEventSchema[]
  total: number
  limit: number
  offset: number
}

// ============================================================================
// Generic API Response Types
// ============================================================================

export interface ApiError {
  detail: string
  errorCode?: string
  timestamp?: string
}

export interface PaginationParams {
  limit?: number
  offset?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  hasMore: boolean
}
