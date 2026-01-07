// Trade History Component Types
// These types are used by the UI components, mapped from API responses

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
  id: string | null
  pnl: number
  date: string | null
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

export type SortColumn =
  | 'closedAt'
  | 'entryPrice'
  | 'exitPrice'
  | 'quantity'
  | 'pnl'
  | 'pnlPercent'
  | 'duration'
export type SortDirection = 'asc' | 'desc'

export interface SortConfig {
  column: SortColumn
  direction: SortDirection
}

// Component Props
export interface TradeHistoryProps {
  performanceMetrics: PerformanceMetrics
  trades: Trade[]
  cumulativePnlData: CumulativePnlDataPoint[]
  filters?: TradeFilters
  sortConfig?: SortConfig
  currentPage?: number
  tradesPerPage?: number
  totalTrades?: number
  isLoading?: boolean
  onPeriodChange?: (
    period: TimePeriod,
    customRange?: { startDate: string; endDate: string }
  ) => void
  onFiltersChange?: (filters: TradeFilters) => void
  onSortChange?: (sortConfig: SortConfig) => void
  onViewTradeDetails?: (tradeId: string) => void
  onSearch?: (query: string) => void
  onClearFilters?: () => void
  onRemoveFilter?: (filterKey: keyof TradeFilters) => void
  onPageChange?: (page: number) => void
}
