// =============================================================================
// Data Types
// =============================================================================

export type BotStatus = 'ACTIVE' | 'PAUSED' | 'STOPPED' | 'WAIT'

export interface BotStatusData {
  status: BotStatus
  stateDescription: string
  cycleActivatedAt: string
  lastUpdate: string
}

export type MacdSignal = 'bullish' | 'bearish'

export interface MarketData {
  btcPrice: number
  priceChange24h: number
  fundingRate: number
  fundingInterval: string
  macdSignal: MacdSignal
  gridRangeLow: number
  gridRangeHigh: number
}

export interface TodayMetrics {
  realizedPnl: number
  pnlPercent: number
  tradesClosed: number
}

export interface TotalMetrics {
  totalPnl: number
  totalTrades: number
  avgProfitPerTrade: number
}

export interface PerformanceMetrics {
  today: TodayMetrics
  total: TotalMetrics
}

export type PositionSide = 'LONG' | 'SHORT'

export interface Position {
  id: string
  entryPrice: number
  currentPrice: number
  quantity: number
  side: PositionSide
  unrealizedPnl: number
  pnlPercent: number
  takeProfitPrice: number
  liquidationPrice: number
  openedAt: string
}

export type OrderSide = 'BUY' | 'SELL'
export type OrderStatus = 'OPEN' | 'FILLED' | 'CANCELLED' | 'REJECTED'

export interface Order {
  id: string
  price: number
  side: OrderSide
  quantity: number
  status: OrderStatus
  createdAt: string
}

export type ActivityEventType =
  | 'ORDER_FILLED'
  | 'TRADE_CLOSED'
  | 'STRATEGY_PAUSED'
  | 'TP_ADJUSTED'
  | 'CYCLE_ACTIVATED'

export interface ActivityEvent {
  id: string
  type: ActivityEventType
  description: string
  timestamp: string
}

export type TimePeriod = 'today' | '7days' | '30days' | 'custom'

// =============================================================================
// Component Props
// =============================================================================

export interface DashboardProps {
  /** Current bot status and state information */
  botStatus: BotStatusData
  /** Real-time market data and conditions */
  marketData: MarketData
  /** Performance metrics for selected time period */
  performanceMetrics: PerformanceMetrics
  /** Currently open positions */
  positions: Position[]
  /** Active grid orders */
  orders: Order[]
  /** Recent trading activity and events */
  activityEvents: ActivityEvent[]
  /** Selected time period for filtering data */
  selectedPeriod?: TimePeriod
  /** Called when user changes the time period filter */
  onPeriodChange?: (period: TimePeriod) => void
  /** Called when user wants to pause the bot */
  onPause?: () => void
  /** Called when user wants to stop the bot */
  onStop?: () => void
  /** Called when user wants to resume the bot */
  onResume?: () => void
  /** Called when user wants to start the bot */
  onStart?: () => void
  /** Called when user clicks a position to view details */
  onViewPosition?: (positionId: string) => void
  /** Called when user wants to cancel an order */
  onCancelOrder?: (orderId: string) => void
}
