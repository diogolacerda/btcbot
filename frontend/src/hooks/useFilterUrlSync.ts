/**
 * Hook for syncing trade filters with URL search params (FE-TRADE-003)
 *
 * Enables bookmarkable filter state by reading/writing URL params.
 * Filters are restored from URL on page load and updated on change.
 */

import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import type {
  TradeFilters,
  SortConfig,
  TimePeriod,
  TradeFilterStatus,
  TradeProfitFilter,
  SortColumn,
  SortDirection,
} from '@/components/trade-history/types'

// =============================================================================
// URL Param Keys
// =============================================================================

const URL_PARAMS = {
  period: 'period',
  startDate: 'startDate',
  endDate: 'endDate',
  status: 'status',
  profitFilter: 'profit',
  minEntryPrice: 'minPrice',
  maxEntryPrice: 'maxPrice',
  minDuration: 'minDuration',
  maxDuration: 'maxDuration',
  minQuantity: 'minQty',
  maxQuantity: 'maxQty',
  searchQuery: 'q',
  sortBy: 'sortBy',
  sortDir: 'sortDir',
  page: 'page',
} as const

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

// =============================================================================
// Validation Helpers
// =============================================================================

function isValidPeriod(value: string | null): value is TimePeriod {
  return value === 'today' || value === '7days' || value === '30days' || value === 'custom'
}

function isValidStatus(value: string | null): value is TradeFilterStatus {
  return value === 'all' || value === 'closed' || value === 'open'
}

function isValidProfitFilter(value: string | null): value is TradeProfitFilter {
  return value === 'all' || value === 'profitable' || value === 'losses'
}

function isValidSortColumn(value: string | null): value is SortColumn {
  const validColumns: SortColumn[] = [
    'closedAt',
    'entryPrice',
    'exitPrice',
    'quantity',
    'pnl',
    'pnlPercent',
    'duration',
  ]
  return validColumns.includes(value as SortColumn)
}

function isValidSortDirection(value: string | null): value is SortDirection {
  return value === 'asc' || value === 'desc'
}

function parseNumber(value: string | null): number | undefined {
  if (!value) return undefined
  const num = parseFloat(value)
  return isNaN(num) ? undefined : num
}

function parseInteger(value: string | null): number | undefined {
  if (!value) return undefined
  const num = parseInt(value, 10)
  return isNaN(num) ? undefined : num
}

// =============================================================================
// Hook
// =============================================================================

interface UseFilterUrlSyncOptions {
  defaultFilters?: TradeFilters
  defaultSort?: SortConfig
}

interface UseFilterUrlSyncReturn {
  filters: TradeFilters
  sortConfig: SortConfig
  currentPage: number
  setFilters: (filters: TradeFilters) => void
  setSortConfig: (sortConfig: SortConfig) => void
  setCurrentPage: (page: number) => void
  clearFilters: () => void
  removeFilter: (filterKey: keyof TradeFilters) => void
}

export function useFilterUrlSync(
  options: UseFilterUrlSyncOptions = {}
): UseFilterUrlSyncReturn {
  const { defaultFilters = DEFAULT_FILTERS, defaultSort = DEFAULT_SORT } = options
  const [searchParams, setSearchParams] = useSearchParams()

  // Parse filters from URL params
  const filters = useMemo((): TradeFilters => {
    const result: TradeFilters = { ...defaultFilters }

    // Period
    const period = searchParams.get(URL_PARAMS.period)
    if (isValidPeriod(period)) {
      result.period = period
    }

    // Custom date range
    const startDate = searchParams.get(URL_PARAMS.startDate)
    const endDate = searchParams.get(URL_PARAMS.endDate)
    if (result.period === 'custom' && startDate && endDate) {
      result.customDateRange = { startDate, endDate }
    }

    // Status
    const status = searchParams.get(URL_PARAMS.status)
    if (isValidStatus(status)) {
      result.status = status
    }

    // Profit filter
    const profitFilter = searchParams.get(URL_PARAMS.profitFilter)
    if (isValidProfitFilter(profitFilter)) {
      result.profitFilter = profitFilter
    }

    // Entry price range
    const minEntryPrice = parseNumber(searchParams.get(URL_PARAMS.minEntryPrice))
    const maxEntryPrice = parseNumber(searchParams.get(URL_PARAMS.maxEntryPrice))
    if (minEntryPrice !== undefined || maxEntryPrice !== undefined) {
      result.entryPriceRange = {
        min: minEntryPrice ?? 0,
        max: maxEntryPrice ?? Infinity,
      }
    }

    // Duration range
    const minDuration = parseInteger(searchParams.get(URL_PARAMS.minDuration))
    const maxDuration = parseInteger(searchParams.get(URL_PARAMS.maxDuration))
    if (minDuration !== undefined || maxDuration !== undefined) {
      result.durationRange = {
        min: minDuration ?? 0,
        max: maxDuration ?? Infinity,
      }
    }

    // Quantity range
    const minQuantity = parseNumber(searchParams.get(URL_PARAMS.minQuantity))
    const maxQuantity = parseNumber(searchParams.get(URL_PARAMS.maxQuantity))
    if (minQuantity !== undefined || maxQuantity !== undefined) {
      result.quantityRange = {
        min: minQuantity ?? 0,
        max: maxQuantity ?? Infinity,
      }
    }

    // Search query
    const searchQuery = searchParams.get(URL_PARAMS.searchQuery)
    if (searchQuery) {
      result.searchQuery = searchQuery
    }

    return result
  }, [searchParams, defaultFilters])

  // Parse sort config from URL params
  const sortConfig = useMemo((): SortConfig => {
    const sortBy = searchParams.get(URL_PARAMS.sortBy)
    const sortDir = searchParams.get(URL_PARAMS.sortDir)

    return {
      column: isValidSortColumn(sortBy) ? sortBy : defaultSort.column,
      direction: isValidSortDirection(sortDir) ? sortDir : defaultSort.direction,
    }
  }, [searchParams, defaultSort])

  // Parse current page from URL params
  const currentPage = useMemo((): number => {
    const page = parseInteger(searchParams.get(URL_PARAMS.page))
    return page && page > 0 ? page : 1
  }, [searchParams])

  // Update URL params when filters change
  const setFilters = useCallback(
    (newFilters: TradeFilters) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev)

          // Period
          if (newFilters.period && newFilters.period !== defaultFilters.period) {
            params.set(URL_PARAMS.period, newFilters.period)
          } else {
            params.delete(URL_PARAMS.period)
          }

          // Custom date range
          if (newFilters.period === 'custom' && newFilters.customDateRange) {
            params.set(URL_PARAMS.startDate, newFilters.customDateRange.startDate)
            params.set(URL_PARAMS.endDate, newFilters.customDateRange.endDate)
          } else {
            params.delete(URL_PARAMS.startDate)
            params.delete(URL_PARAMS.endDate)
          }

          // Status
          if (newFilters.status && newFilters.status !== 'all') {
            params.set(URL_PARAMS.status, newFilters.status)
          } else {
            params.delete(URL_PARAMS.status)
          }

          // Profit filter
          if (newFilters.profitFilter && newFilters.profitFilter !== 'all') {
            params.set(URL_PARAMS.profitFilter, newFilters.profitFilter)
          } else {
            params.delete(URL_PARAMS.profitFilter)
          }

          // Entry price range
          if (newFilters.entryPriceRange) {
            if (newFilters.entryPriceRange.min > 0) {
              params.set(URL_PARAMS.minEntryPrice, newFilters.entryPriceRange.min.toString())
            } else {
              params.delete(URL_PARAMS.minEntryPrice)
            }
            if (newFilters.entryPriceRange.max !== Infinity) {
              params.set(URL_PARAMS.maxEntryPrice, newFilters.entryPriceRange.max.toString())
            } else {
              params.delete(URL_PARAMS.maxEntryPrice)
            }
          } else {
            params.delete(URL_PARAMS.minEntryPrice)
            params.delete(URL_PARAMS.maxEntryPrice)
          }

          // Duration range
          if (newFilters.durationRange) {
            if (newFilters.durationRange.min > 0) {
              params.set(URL_PARAMS.minDuration, newFilters.durationRange.min.toString())
            } else {
              params.delete(URL_PARAMS.minDuration)
            }
            if (newFilters.durationRange.max !== Infinity) {
              params.set(URL_PARAMS.maxDuration, newFilters.durationRange.max.toString())
            } else {
              params.delete(URL_PARAMS.maxDuration)
            }
          } else {
            params.delete(URL_PARAMS.minDuration)
            params.delete(URL_PARAMS.maxDuration)
          }

          // Quantity range
          if (newFilters.quantityRange) {
            if (newFilters.quantityRange.min > 0) {
              params.set(URL_PARAMS.minQuantity, newFilters.quantityRange.min.toString())
            } else {
              params.delete(URL_PARAMS.minQuantity)
            }
            if (newFilters.quantityRange.max !== Infinity) {
              params.set(URL_PARAMS.maxQuantity, newFilters.quantityRange.max.toString())
            } else {
              params.delete(URL_PARAMS.maxQuantity)
            }
          } else {
            params.delete(URL_PARAMS.minQuantity)
            params.delete(URL_PARAMS.maxQuantity)
          }

          // Search query
          if (newFilters.searchQuery) {
            params.set(URL_PARAMS.searchQuery, newFilters.searchQuery)
          } else {
            params.delete(URL_PARAMS.searchQuery)
          }

          // Reset to page 1 on filter change
          params.delete(URL_PARAMS.page)

          return params
        },
        { replace: true }
      )
    },
    [setSearchParams, defaultFilters]
  )

  // Update URL params when sort config changes
  const setSortConfig = useCallback(
    (newSortConfig: SortConfig) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev)

          if (newSortConfig.column !== defaultSort.column) {
            params.set(URL_PARAMS.sortBy, newSortConfig.column)
          } else {
            params.delete(URL_PARAMS.sortBy)
          }

          if (newSortConfig.direction !== defaultSort.direction) {
            params.set(URL_PARAMS.sortDir, newSortConfig.direction)
          } else {
            params.delete(URL_PARAMS.sortDir)
          }

          return params
        },
        { replace: true }
      )
    },
    [setSearchParams, defaultSort]
  )

  // Update URL params when page changes
  const setCurrentPage = useCallback(
    (page: number) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev)

          if (page > 1) {
            params.set(URL_PARAMS.page, page.toString())
          } else {
            params.delete(URL_PARAMS.page)
          }

          return params
        },
        { replace: true }
      )
    },
    [setSearchParams]
  )

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)

        // Remove all filter params
        Object.values(URL_PARAMS).forEach((key) => {
          if (key !== URL_PARAMS.sortBy && key !== URL_PARAMS.sortDir) {
            params.delete(key)
          }
        })

        return params
      },
      { replace: true }
    )
  }, [setSearchParams])

  // Remove a specific filter
  const removeFilter = useCallback(
    (filterKey: keyof TradeFilters) => {
      const newFilters = { ...filters }
      delete newFilters[filterKey]

      // Special handling for related fields
      if (filterKey === 'period' || filterKey === 'customDateRange') {
        delete newFilters.period
        delete newFilters.customDateRange
      }

      setFilters(newFilters)
    },
    [filters, setFilters]
  )

  return {
    filters,
    sortConfig,
    currentPage,
    setFilters,
    setSortConfig,
    setCurrentPage,
    clearFilters,
    removeFilter,
  }
}
