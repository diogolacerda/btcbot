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
