// =============================================================================
// Data Types
// =============================================================================

export type TradeSide = 'LONG' | 'SHORT'
export type TradeStatus = 'CLOSED' | 'OPEN'
export type TimePeriod = 'today' | '7days' | '30days' | 'custom'
export type TradeFilterStatus = 'all' | 'closed' | 'open'
export type TradeProfitFilter = 'all' | 'profitable' | 'losses'

export interface TpAdjustment {
  timestamp: string
  oldTp: number
  newTp: number
  reason: string
}

export interface TradeFees {
  tradingFee: number
  fundingFee: number
  netPnl: number
}

export interface Trade {
  id: string
  orderId: string
  tpOrderId: string
  symbol: string
  side: TradeSide
  leverage: number
  entryPrice: number
  exitPrice: number
  quantity: number
  pnl: number
  pnlPercent: number
  status: TradeStatus
  openedAt: string
  filledAt: string
  closedAt: string
  duration: number
  fees: TradeFees
  tpAdjustments: TpAdjustment[]
}

export interface BestWorstTrade {
  id: string
  pnl: number
  date: string
}

export interface PerformanceMetrics {
  totalPnl: number
  roi: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  avgProfit: number
  bestTrade: BestWorstTrade
  worstTrade: BestWorstTrade
}

export interface CumulativePnlDataPoint {
  date: string
  cumulativePnl: number
}

export interface TradeFilters {
  period?: TimePeriod
  customDateRange?: { startDate: string; endDate: string }
  status?: TradeFilterStatus
  profitFilter?: TradeProfitFilter
  entryPriceRange?: { min: number; max: number }
  durationRange?: { min: number; max: number }
  quantityRange?: { min: number; max: number }
  searchQuery?: string
}

export type SortColumn = 'closedAt' | 'entryPrice' | 'exitPrice' | 'quantity' | 'pnl' | 'pnlPercent' | 'duration'
export type SortDirection = 'asc' | 'desc'

export interface SortConfig {
  column: SortColumn
  direction: SortDirection
}

// =============================================================================
// Component Props
// =============================================================================

export interface TradeHistoryProps {
  /** Performance metrics aggregated from trades */
  performanceMetrics: PerformanceMetrics
  /** List of all trades */
  trades: Trade[]
  /** Cumulative P&L data points for chart */
  cumulativePnlData: CumulativePnlDataPoint[]
  /** Currently active filters */
  filters?: TradeFilters
  /** Current sorting configuration */
  sortConfig?: SortConfig
  /** Current page number for pagination */
  currentPage?: number
  /** Number of trades per page */
  tradesPerPage?: number
  /** Called when user changes time period */
  onPeriodChange?: (period: TimePeriod, customRange?: { startDate: string; endDate: string }) => void
  /** Called when user updates filters */
  onFiltersChange?: (filters: TradeFilters) => void
  /** Called when user changes sorting */
  onSortChange?: (sortConfig: SortConfig) => void
  /** Called when user clicks a trade to view details */
  onViewTradeDetails?: (tradeId: string) => void
  /** Called when user searches by order ID */
  onSearch?: (query: string) => void
  /** Called when user clears all filters */
  onClearFilters?: () => void
  /** Called when user removes a specific filter */
  onRemoveFilter?: (filterKey: keyof TradeFilters) => void
  /** Called when user changes page */
  onPageChange?: (page: number) => void
}
