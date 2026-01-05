/**
 * Dashboard Data Fetching Hooks (FE-DASH-001)
 *
 * TanStack Query hooks for fetching all dashboard data with proper caching,
 * loading states, and error handling.
 */

import { useQuery } from '@tanstack/react-query'
import { axiosInstance } from '../lib/axios'
import { parseApiResponse } from '../lib/transformers'
import type {
  BotStatusResponse,
  PriceResponse,
  FundingRateResponse,
  MACDDataResponse,
  GridRangeResponse,
  PerformanceMetricsResponse,
  OrdersListResponse,
  ActivityEventsListResponse,
  TimePeriod,
  OrderStatusEnum,
} from '../types/api'

// ============================================================================
// Query Keys - Centralized for cache invalidation
// ============================================================================

export const dashboardKeys = {
  all: ['dashboard'] as const,
  botStatus: () => [...dashboardKeys.all, 'bot-status'] as const,
  marketData: () => [...dashboardKeys.all, 'market-data'] as const,
  price: () => [...dashboardKeys.marketData(), 'price'] as const,
  funding: () => [...dashboardKeys.marketData(), 'funding'] as const,
  macd: () => [...dashboardKeys.marketData(), 'macd'] as const,
  gridRange: () => [...dashboardKeys.marketData(), 'grid-range'] as const,
  metrics: (period: TimePeriod) => [...dashboardKeys.all, 'metrics', period] as const,
  orders: (status?: OrderStatusEnum) => [...dashboardKeys.all, 'orders', status] as const,
  positions: () => [...dashboardKeys.all, 'positions'] as const,
  activity: (period: TimePeriod, limit?: number) =>
    [...dashboardKeys.all, 'activity', period, limit] as const,
}

// ============================================================================
// Bot Status Hook
// ============================================================================

/**
 * Fetch current bot status including state, MACD values, and order stats.
 * Polls every 5 seconds when enabled.
 */
export function useBotStatus(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: dashboardKeys.botStatus(),
    queryFn: async () => {
      const response = await axiosInstance.get('/bot/status')
      return parseApiResponse<BotStatusResponse>(response.data)
    },
    staleTime: 5 * 1000, // 5 seconds - status changes frequently
    refetchInterval: options?.refetchInterval ?? 5000, // Poll every 5s
    enabled: options?.enabled ?? true,
  })
}

// ============================================================================
// Market Data Hooks
// ============================================================================

/**
 * Fetch current BTC price with 24h statistics.
 * Cached for 30 seconds.
 */
export function usePrice(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: dashboardKeys.price(),
    queryFn: async () => {
      const response = await axiosInstance.get('/market/price')
      return parseApiResponse<PriceResponse>(response.data)
    },
    staleTime: 30 * 1000, // 30 seconds
    enabled: options?.enabled ?? true,
  })
}

/**
 * Fetch current funding rate data.
 * Cached for 5 minutes (funding rate changes slowly).
 */
export function useFundingRate(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: dashboardKeys.funding(),
    queryFn: async () => {
      const response = await axiosInstance.get('/market/funding')
      return parseApiResponse<FundingRateResponse>(response.data)
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: options?.enabled ?? true,
  })
}

/**
 * Fetch current MACD indicator values.
 * Cached for 1 minute.
 */
export function useMACDData(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: dashboardKeys.macd(),
    queryFn: async () => {
      const response = await axiosInstance.get('/market/macd')
      return parseApiResponse<MACDDataResponse>(response.data)
    },
    staleTime: 60 * 1000, // 1 minute
    enabled: options?.enabled ?? true,
  })
}

/**
 * Fetch current grid range configuration.
 * Cached for 1 minute.
 */
export function useGridRange(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: dashboardKeys.gridRange(),
    queryFn: async () => {
      const response = await axiosInstance.get('/market/grid-range')
      return parseApiResponse<GridRangeResponse>(response.data)
    },
    staleTime: 60 * 1000, // 1 minute
    enabled: options?.enabled ?? true,
  })
}

/**
 * Combined hook to fetch all market data in parallel.
 * Returns individual query results for granular loading states.
 */
export function useMarketData(options?: { enabled?: boolean }) {
  const priceQuery = usePrice(options)
  const fundingQuery = useFundingRate(options)
  const macdQuery = useMACDData(options)
  const gridRangeQuery = useGridRange(options)

  return {
    price: priceQuery,
    funding: fundingQuery,
    macd: macdQuery,
    gridRange: gridRangeQuery,
    isLoading:
      priceQuery.isLoading ||
      fundingQuery.isLoading ||
      macdQuery.isLoading ||
      gridRangeQuery.isLoading,
    isError:
      priceQuery.isError ||
      fundingQuery.isError ||
      macdQuery.isError ||
      gridRangeQuery.isError,
  }
}

// ============================================================================
// Performance Metrics Hook
// ============================================================================

interface PerformanceMetricsOptions {
  period?: TimePeriod
  startDate?: string
  endDate?: string
  enabled?: boolean
}

/**
 * Fetch performance metrics for a given time period.
 * Supports predefined periods (today, 7days, 30days) or custom date range.
 */
export function usePerformanceMetrics(options?: PerformanceMetricsOptions) {
  const period = options?.period ?? 'today'

  return useQuery({
    queryKey: dashboardKeys.metrics(period),
    queryFn: async () => {
      const params: Record<string, string> = { period }
      if (period === 'custom' && options?.startDate && options?.endDate) {
        params.start_date = options.startDate
        params.end_date = options.endDate
      }
      const response = await axiosInstance.get('/metrics/performance', { params })
      return parseApiResponse<PerformanceMetricsResponse>(response.data)
    },
    staleTime: 60 * 1000, // 1 minute
    enabled: options?.enabled ?? true,
  })
}

// ============================================================================
// Orders Hook
// ============================================================================

interface OrdersOptions {
  status?: OrderStatusEnum
  limit?: number
  offset?: number
  enabled?: boolean
}

/**
 * Fetch active grid orders with optional status filtering.
 * Returns both pending limit orders and filled positions with TP orders.
 */
export function useOrders(options?: OrdersOptions) {
  return useQuery({
    queryKey: dashboardKeys.orders(options?.status),
    queryFn: async () => {
      const params: Record<string, string | number> = {}
      if (options?.status) params.status = options.status
      if (options?.limit) params.limit = options.limit
      if (options?.offset) params.offset = options.offset

      const response = await axiosInstance.get('/orders', { params })
      return parseApiResponse<OrdersListResponse>(response.data)
    },
    staleTime: 10 * 1000, // 10 seconds - orders change frequently
    enabled: options?.enabled ?? true,
  })
}

/**
 * Fetch only filled orders (open positions awaiting TP).
 * Convenience wrapper around useOrders.
 */
export function usePositions(options?: { limit?: number; offset?: number; enabled?: boolean }) {
  return useOrders({
    status: 'FILLED',
    limit: options?.limit,
    offset: options?.offset,
    enabled: options?.enabled,
  })
}

// ============================================================================
// Activity Events Hook
// ============================================================================

interface ActivityEventsOptions {
  period?: TimePeriod
  startDate?: string
  endDate?: string
  limit?: number
  offset?: number
  enabled?: boolean
}

/**
 * Fetch recent trading activity events.
 * Supports time period filtering and pagination.
 */
export function useActivityEvents(options?: ActivityEventsOptions) {
  const period = options?.period ?? 'today'
  const limit = options?.limit ?? 50

  return useQuery({
    queryKey: dashboardKeys.activity(period, limit),
    queryFn: async () => {
      const params: Record<string, string | number> = {
        period,
        limit,
      }
      if (options?.offset) params.offset = options.offset
      if (period === 'custom' && options?.startDate && options?.endDate) {
        params.start_date = options.startDate
        params.end_date = options.endDate
      }

      const response = await axiosInstance.get('/activity', { params })
      return parseApiResponse<ActivityEventsListResponse>(response.data)
    },
    staleTime: 30 * 1000, // 30 seconds
    enabled: options?.enabled ?? true,
  })
}
