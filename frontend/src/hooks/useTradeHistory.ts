/**
 * Trade History Data Fetching Hooks (FE-TRADE-001)
 *
 * TanStack Query hooks for fetching Trade History data with filtering,
 * sorting, and pagination. Includes hooks for performance metrics and
 * cumulative P&L chart data.
 */

import { useQuery } from '@tanstack/react-query'
import { axiosInstance } from '../lib/axios'
import { parseApiResponse } from '../lib/transformers'
import type {
  EnhancedTradesListResponse,
  TradesFilterParams,
  TradesSortConfig,
  TradesPaginationParams,
  TradePerformanceMetricsResponse,
  CumulativePnlResponse,
  TimePeriod,
} from '../types/api'

// ============================================================================
// Query Keys - Centralized for cache invalidation
// ============================================================================

export const tradeHistoryKeys = {
  all: ['trade-history'] as const,
  trades: (
    filters?: TradesFilterParams,
    sort?: TradesSortConfig,
    pagination?: TradesPaginationParams
  ) => [...tradeHistoryKeys.all, 'trades', filters, sort, pagination] as const,
  performanceMetrics: (period: TimePeriod, startDate?: string, endDate?: string) =>
    [...tradeHistoryKeys.all, 'performance-metrics', period, startDate, endDate] as const,
  cumulativePnl: (period: TimePeriod, startDate?: string, endDate?: string) =>
    [...tradeHistoryKeys.all, 'cumulative-pnl', period, startDate, endDate] as const,
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Build query params for the trades endpoint.
 * Converts camelCase filter params to snake_case for the API.
 */
function buildTradesQueryParams(
  filters?: TradesFilterParams,
  sort?: TradesSortConfig,
  pagination?: TradesPaginationParams
): Record<string, string | number> {
  const params: Record<string, string | number> = {}

  // Pagination params
  if (pagination?.limit) params.limit = pagination.limit
  if (pagination?.offset) params.offset = pagination.offset

  // Sort params - convert camelCase field names to snake_case for API
  if (sort?.sortBy) {
    // Map frontend camelCase to backend camelCase (API uses camelCase in query params)
    params.sort_by = sort.sortBy
  }
  if (sort?.sortDirection) params.sort_direction = sort.sortDirection

  // Filter params
  if (filters?.status) params.status = filters.status
  if (filters?.startDate) params.start_date = filters.startDate
  if (filters?.endDate) params.end_date = filters.endDate
  if (filters?.profitFilter) params.profit_filter = filters.profitFilter
  if (filters?.minEntryPrice) params.min_entry_price = filters.minEntryPrice
  if (filters?.maxEntryPrice) params.max_entry_price = filters.maxEntryPrice
  if (filters?.minDuration) params.min_duration = filters.minDuration
  if (filters?.maxDuration) params.max_duration = filters.maxDuration
  if (filters?.minQuantity) params.min_quantity = filters.minQuantity
  if (filters?.maxQuantity) params.max_quantity = filters.maxQuantity
  if (filters?.searchQuery) params.search_query = filters.searchQuery

  return params
}

// ============================================================================
// useTrades Hook
// ============================================================================

export interface UseTradesOptions {
  filters?: TradesFilterParams
  sort?: TradesSortConfig
  pagination?: TradesPaginationParams
  enabled?: boolean
}

/**
 * Fetch trades with advanced filtering, sorting, and pagination.
 *
 * Supports 5 filter types:
 * - profitFilter: Filter by profit/loss status (all, profitable, losses)
 * - price range: Filter by min/max entry price
 * - duration range: Filter by min/max trade duration in seconds
 * - quantity range: Filter by min/max quantity
 * - searchQuery: Search by exchange_order_id or exchange_tp_order_id
 *
 * Supports sorting by 7 columns:
 * - closedAt (default): Sort by close timestamp
 * - entryPrice: Sort by entry price
 * - exitPrice: Sort by exit price
 * - quantity: Sort by trade quantity
 * - pnl: Sort by profit/loss amount
 * - pnlPercent: Sort by profit/loss percentage
 * - duration: Sort by trade duration
 *
 * Caching: staleTime 30s, gcTime 5min
 */
export function useTrades(options?: UseTradesOptions) {
  const { filters, sort, pagination, enabled = true } = options ?? {}

  return useQuery({
    queryKey: tradeHistoryKeys.trades(filters, sort, pagination),
    queryFn: async () => {
      const params = buildTradesQueryParams(filters, sort, pagination)
      const response = await axiosInstance.get('/trading/trades', { params })
      return parseApiResponse<EnhancedTradesListResponse>(response.data)
    },
    staleTime: 30 * 1000, // 30 seconds - trades don't change frequently
    gcTime: 5 * 60 * 1000, // 5 minutes cache
    enabled,
    retry: 2,
  })
}

// ============================================================================
// usePerformanceMetrics Hook
// ============================================================================

export interface UsePerformanceMetricsOptions {
  period?: TimePeriod
  startDate?: string
  endDate?: string
  enabled?: boolean
}

/**
 * Fetch performance metrics for a given time period.
 *
 * Includes:
 * - Total P&L and ROI
 * - Win rate and trade counts
 * - Best and worst trades with full details
 *
 * Supports predefined periods (today, 7days, 30days) or custom date range.
 *
 * Caching: staleTime 60s, gcTime 5min
 */
export function usePerformanceMetrics(options?: UsePerformanceMetricsOptions) {
  const { period = 'today', startDate, endDate, enabled = true } = options ?? {}

  return useQuery({
    queryKey: tradeHistoryKeys.performanceMetrics(period, startDate, endDate),
    queryFn: async () => {
      const params: Record<string, string> = { period }
      if (period === 'custom' && startDate && endDate) {
        params.start_date = startDate
        params.end_date = endDate
      }
      const response = await axiosInstance.get('/trading/performance-metrics', { params })
      return parseApiResponse<TradePerformanceMetricsResponse>(response.data)
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes cache
    enabled,
    retry: 2,
  })
}

// ============================================================================
// useCumulativePnl Hook
// ============================================================================

export interface UseCumulativePnlOptions {
  period?: TimePeriod
  startDate?: string
  endDate?: string
  enabled?: boolean
}

/**
 * Fetch cumulative P&L data for charting equity curve.
 *
 * Returns daily data points with running cumulative P&L totals.
 * Each point represents the total P&L from the start of the period
 * up to and including that date.
 *
 * Ideal for plotting an equity curve chart showing the account's
 * performance over time.
 *
 * Caching: staleTime 60s, gcTime 5min
 */
export function useCumulativePnl(options?: UseCumulativePnlOptions) {
  const { period = '30days', startDate, endDate, enabled = true } = options ?? {}

  return useQuery({
    queryKey: tradeHistoryKeys.cumulativePnl(period, startDate, endDate),
    queryFn: async () => {
      const params: Record<string, string> = { period }
      if (period === 'custom' && startDate && endDate) {
        params.start_date = startDate
        params.end_date = endDate
      }
      const response = await axiosInstance.get('/trading/cumulative-pnl', { params })
      return parseApiResponse<CumulativePnlResponse>(response.data)
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes cache
    enabled,
    retry: 2,
  })
}

// ============================================================================
// Combined Hook for Trade History Page
// ============================================================================

export interface UseTradeHistoryDataOptions {
  tradesOptions?: UseTradesOptions
  metricsOptions?: UsePerformanceMetricsOptions
  cumulativePnlOptions?: UseCumulativePnlOptions
  enabled?: boolean
}

/**
 * Combined hook to fetch all trade history data in parallel.
 * Returns individual query results for granular loading states.
 *
 * Use this when you need all three data sets on the same page.
 */
export function useTradeHistoryData(options?: UseTradeHistoryDataOptions) {
  const { tradesOptions, metricsOptions, cumulativePnlOptions, enabled = true } = options ?? {}

  const tradesQuery = useTrades({
    ...tradesOptions,
    enabled: enabled && (tradesOptions?.enabled ?? true),
  })

  const metricsQuery = usePerformanceMetrics({
    ...metricsOptions,
    enabled: enabled && (metricsOptions?.enabled ?? true),
  })

  const cumulativePnlQuery = useCumulativePnl({
    ...cumulativePnlOptions,
    enabled: enabled && (cumulativePnlOptions?.enabled ?? true),
  })

  return {
    trades: tradesQuery,
    metrics: metricsQuery,
    cumulativePnl: cumulativePnlQuery,
    isLoading:
      tradesQuery.isLoading || metricsQuery.isLoading || cumulativePnlQuery.isLoading,
    isError: tradesQuery.isError || metricsQuery.isError || cumulativePnlQuery.isError,
  }
}
