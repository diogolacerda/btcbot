/**
 * Trade History Page (FE-TRADE-002, FE-TRADE-003)
 *
 * Integrates trade history components with data fetching hooks.
 * Implements state management for filters, sorting, and pagination.
 * Syncs filter state with URL params for bookmarkable URLs (FE-TRADE-003).
 */

import { useCallback, useMemo } from 'react'
import { TradeHistory } from '@/components/trade-history'
import type {
  Trade,
  TradeFilters,
  SortConfig,
  TimePeriod,
  PerformanceMetrics,
  CumulativePnlDataPoint,
} from '@/components/trade-history/types'
import {
  useTrades,
  usePerformanceMetrics,
  useCumulativePnl,
} from '@/hooks/useTradeHistory'
import { useFilterUrlSync } from '@/hooks/useFilterUrlSync'
import type {
  EnhancedTradeSchema,
  TradesFilterParams,
  TradesSortConfig,
  TradePerformanceMetricsResponse,
  CumulativePnlResponse,
  TimePeriod as ApiTimePeriod,
  ProfitFilter,
  SortByField,
} from '@/types/api'

// =============================================================================
// Data Transformers - Map API responses to component types
// =============================================================================

/**
 * Transform API trade schema to component Trade type
 */
function transformTrade(apiTrade: EnhancedTradeSchema): Trade {
  return {
    id: apiTrade.id,
    orderId: apiTrade.exchangeOrderId || 'N/A',
    tpOrderId: apiTrade.exchangeTpOrderId || 'N/A',
    symbol: apiTrade.symbol,
    side: apiTrade.side,
    leverage: apiTrade.leverage,
    entryPrice: apiTrade.entryPrice,
    exitPrice: apiTrade.exitPrice || 0,
    quantity: apiTrade.quantity,
    pnl: apiTrade.pnl || 0,
    pnlPercent: apiTrade.pnlPercent || 0,
    status: apiTrade.status === 'CLOSED' ? 'CLOSED' : 'OPEN',
    openedAt: apiTrade.openedAt,
    filledAt: apiTrade.filledAt || apiTrade.openedAt,
    closedAt: apiTrade.closedAt || apiTrade.updatedAt,
    duration: apiTrade.duration || 0,
    fees: apiTrade.fees || {
      tradingFee: apiTrade.tradingFee,
      fundingFee: apiTrade.fundingFee,
      netPnl: (apiTrade.pnl || 0) - apiTrade.tradingFee - apiTrade.fundingFee,
    },
    tpAdjustments: apiTrade.tpAdjustments.map((adj) => ({
      timestamp: adj.timestamp,
      oldTp: adj.oldTp,
      newTp: adj.newTp,
      reason: adj.reason,
    })),
  }
}

/**
 * Transform API performance metrics to component type
 */
function transformPerformanceMetrics(
  apiMetrics: TradePerformanceMetricsResponse
): PerformanceMetrics {
  return {
    totalPnl: apiMetrics.totalPnl,
    roi: apiMetrics.roi,
    totalTrades: apiMetrics.totalTrades,
    winningTrades: apiMetrics.winningTrades,
    losingTrades: apiMetrics.losingTrades,
    winRate: apiMetrics.winRate,
    avgProfit: apiMetrics.avgProfit,
    bestTrade: {
      id: apiMetrics.bestTrade.id,
      pnl: apiMetrics.bestTrade.pnl,
      date: apiMetrics.bestTrade.date,
    },
    worstTrade: {
      id: apiMetrics.worstTrade.id,
      pnl: apiMetrics.worstTrade.pnl,
      date: apiMetrics.worstTrade.date,
    },
  }
}

/**
 * Transform API cumulative P&L data to component type
 */
function transformCumulativePnl(
  apiData: CumulativePnlResponse
): CumulativePnlDataPoint[] {
  return apiData.data.map((point) => ({
    date: point.date,
    cumulativePnl: point.cumulativePnl,
  }))
}

/**
 * Transform component filters to API filter params
 */
function transformFiltersToApi(filters: TradeFilters): TradesFilterParams {
  const apiFilters: TradesFilterParams = {}

  // Status filter
  if (filters.status === 'closed') {
    apiFilters.status = 'CLOSED'
  } else if (filters.status === 'open') {
    apiFilters.status = 'OPEN'
  }

  // Date filters
  if (filters.period === 'custom' && filters.customDateRange) {
    apiFilters.startDate = filters.customDateRange.startDate
    apiFilters.endDate = filters.customDateRange.endDate
  } else if (filters.period === 'today') {
    const today = new Date().toISOString().split('T')[0]
    apiFilters.startDate = today
    apiFilters.endDate = today
  } else if (filters.period === '7days') {
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - 7)
    apiFilters.startDate = start.toISOString().split('T')[0]
    apiFilters.endDate = end.toISOString().split('T')[0]
  } else if (filters.period === '30days') {
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - 30)
    apiFilters.startDate = start.toISOString().split('T')[0]
    apiFilters.endDate = end.toISOString().split('T')[0]
  }

  // Profit filter
  if (filters.profitFilter && filters.profitFilter !== 'all') {
    apiFilters.profitFilter = filters.profitFilter as ProfitFilter
  }

  // Price range
  if (filters.entryPriceRange) {
    if (filters.entryPriceRange.min > 0) {
      apiFilters.minEntryPrice = filters.entryPriceRange.min
    }
    if (filters.entryPriceRange.max !== Infinity) {
      apiFilters.maxEntryPrice = filters.entryPriceRange.max
    }
  }

  // Duration range
  if (filters.durationRange) {
    if (filters.durationRange.min > 0) {
      apiFilters.minDuration = filters.durationRange.min
    }
    if (filters.durationRange.max !== Infinity) {
      apiFilters.maxDuration = filters.durationRange.max
    }
  }

  // Quantity range
  if (filters.quantityRange) {
    if (filters.quantityRange.min > 0) {
      apiFilters.minQuantity = filters.quantityRange.min
    }
    if (filters.quantityRange.max !== Infinity) {
      apiFilters.maxQuantity = filters.quantityRange.max
    }
  }

  // Search query
  if (filters.searchQuery) {
    apiFilters.searchQuery = filters.searchQuery
  }

  return apiFilters
}

/**
 * Transform component sort config to API sort config
 */
function transformSortToApi(sortConfig: SortConfig): TradesSortConfig {
  return {
    sortBy: sortConfig.column as SortByField,
    sortDirection: sortConfig.direction,
  }
}

// =============================================================================
// Default Values
// =============================================================================

const DEFAULT_FILTERS: TradeFilters = {
  period: '30days',
  status: 'all',
  profitFilter: 'all',
}

const DEFAULT_SORT: SortConfig = {
  column: 'closedAt',
  direction: 'desc',
}

const DEFAULT_PERFORMANCE_METRICS: PerformanceMetrics = {
  totalPnl: 0,
  roi: 0,
  totalTrades: 0,
  winningTrades: 0,
  losingTrades: 0,
  winRate: 0,
  avgProfit: 0,
  bestTrade: { id: null, pnl: 0, date: null },
  worstTrade: { id: null, pnl: 0, date: null },
}

const TRADES_PER_PAGE = 50

// =============================================================================
// Component
// =============================================================================

export function TradeHistoryPage() {
  // State management with URL sync (FE-TRADE-003)
  const {
    filters,
    sortConfig,
    currentPage,
    setFilters,
    setSortConfig,
    setCurrentPage,
    clearFilters,
    removeFilter,
  } = useFilterUrlSync({
    defaultFilters: DEFAULT_FILTERS,
    defaultSort: DEFAULT_SORT,
  })

  // Calculate API period from filters
  const apiPeriod: ApiTimePeriod = useMemo(() => {
    return (filters.period || '30days') as ApiTimePeriod
  }, [filters.period])

  // Transform filters for API
  const apiFilters = useMemo(() => transformFiltersToApi(filters), [filters])
  const apiSort = useMemo(() => transformSortToApi(sortConfig), [sortConfig])

  // Data fetching hooks
  const {
    data: tradesData,
    isLoading: isLoadingTrades,
    isError: isTradesError,
  } = useTrades({
    filters: apiFilters,
    sort: apiSort,
    pagination: {
      limit: TRADES_PER_PAGE,
      offset: (currentPage - 1) * TRADES_PER_PAGE,
    },
  })

  const { data: metricsData, isLoading: isLoadingMetrics } = usePerformanceMetrics({
    period: apiPeriod,
    startDate: filters.customDateRange?.startDate,
    endDate: filters.customDateRange?.endDate,
  })

  const { data: pnlData, isLoading: isLoadingPnl } = useCumulativePnl({
    period: apiPeriod,
    startDate: filters.customDateRange?.startDate,
    endDate: filters.customDateRange?.endDate,
  })

  // Transform data for components
  const trades: Trade[] = useMemo(() => {
    if (!tradesData?.trades) return []
    return tradesData.trades.map(transformTrade)
  }, [tradesData])

  const performanceMetrics: PerformanceMetrics = useMemo(() => {
    if (!metricsData) return DEFAULT_PERFORMANCE_METRICS
    return transformPerformanceMetrics(metricsData)
  }, [metricsData])

  const cumulativePnlData: CumulativePnlDataPoint[] = useMemo(() => {
    if (!pnlData) return []
    return transformCumulativePnl(pnlData)
  }, [pnlData])

  const totalTrades = tradesData?.total || 0

  // Callbacks - now using URL-synced state from useFilterUrlSync
  const handlePeriodChange = useCallback(
    (period: TimePeriod, customRange?: { startDate: string; endDate: string }) => {
      setFilters({
        ...filters,
        period,
        customDateRange: customRange,
      })
    },
    [filters, setFilters]
  )

  const handleFiltersChange = useCallback(
    (newFilters: TradeFilters) => {
      setFilters({ ...filters, ...newFilters })
    },
    [filters, setFilters]
  )

  const handleSortChange = useCallback(
    (newSortConfig: SortConfig) => {
      setSortConfig(newSortConfig)
    },
    [setSortConfig]
  )

  const handleViewTradeDetails = useCallback((tradeId: string) => {
    // The TradeHistory component handles showing the modal internally
    console.log('Viewing trade details:', tradeId)
  }, [])

  const handleSearch = useCallback(
    (query: string) => {
      setFilters({ ...filters, searchQuery: query || undefined })
    },
    [filters, setFilters]
  )

  const handleClearFilters = useCallback(() => {
    clearFilters()
  }, [clearFilters])

  const handleRemoveFilter = useCallback(
    (filterKey: keyof TradeFilters) => {
      removeFilter(filterKey)
    },
    [removeFilter]
  )

  const handlePageChange = useCallback(
    (page: number) => {
      setCurrentPage(page)
    },
    [setCurrentPage]
  )

  // Loading state
  const isLoading = isLoadingTrades || isLoadingMetrics || isLoadingPnl

  // Error state
  if (isTradesError) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-red-700 dark:text-red-400 mb-2">
              Error Loading Trade History
            </h2>
            <p className="text-red-600 dark:text-red-300">
              Unable to load trade data. Please try again later.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <TradeHistory
        performanceMetrics={performanceMetrics}
        trades={trades}
        cumulativePnlData={cumulativePnlData}
        filters={filters}
        sortConfig={sortConfig}
        currentPage={currentPage}
        tradesPerPage={TRADES_PER_PAGE}
        totalTrades={totalTrades}
        isLoading={isLoading}
        onPeriodChange={handlePeriodChange}
        onFiltersChange={handleFiltersChange}
        onSortChange={handleSortChange}
        onViewTradeDetails={handleViewTradeDetails}
        onSearch={handleSearch}
        onClearFilters={handleClearFilters}
        onRemoveFilter={handleRemoveFilter}
        onPageChange={handlePageChange}
      />
    </div>
  )
}
