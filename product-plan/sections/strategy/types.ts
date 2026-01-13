// =============================================================================
// Data Types
// =============================================================================

export type StrategyStatus = 'active' | 'paused' | 'stopped' | 'wait'
export type MarginMode = 'crossed' | 'isolated'
export type SpacingType = 'fixed' | 'percentage'
export type GridAnchor = 'none' | 'align-100s'
export type MACDTimeframe = '15m' | '1h' | '4h' | '1d'
export type AutoReactivationMode = 'immediate' | 'full-cycle'
export type LiquidationRisk = 'low' | 'medium' | 'high'
export type GridLevelType = 'buy' | 'sell' | 'current'

export interface Cycle {
  startedAt: string
  pnlSinceStart: number
  tradesSinceStart: number
  winRateSinceStart: number
}

export interface RiskParameters {
  positionSize: number
  maxTotalOrders: number
  leverage: number
  marginMode: MarginMode
}

export interface GridSettings {
  spacingType: SpacingType
  spacingValue: number
  gridRange: number
  takeProfit: number
  gridAnchor: GridAnchor
}

export interface DynamicTPConfig {
  enabled: boolean
  baseTP: number
  minTP: number
  maxTP: number
  safetyMargin: number
  checkInterval: number
}

export interface AdvancedSettings {
  dynamicTP: DynamicTPConfig
  autoReactivationMode: AutoReactivationMode
}

export interface MACDFilter {
  enabled: boolean
  fastPeriod: number
  slowPeriod: number
  signalPeriod: number
  timeframe: MACDTimeframe
}

export interface Strategy {
  id: string
  name: string
  status: StrategyStatus
  statusContext: string
  cycle: Cycle
  lastUpdated: string
  riskParameters: RiskParameters
  gridSettings: GridSettings
  macdFilter: MACDFilter
  advancedSettings: AdvancedSettings
}

export interface CurrentMarket {
  btcPrice: number
  fundingRate: number
  lastUpdate: string
}

export interface RiskSummary {
  totalCapital: number
  capitalPerPosition: number
  liquidationRisk: LiquidationRisk
  maxLossPerTrade: number
  maxLossPerTradePercent: number
}

export interface GridLevel {
  level: number
  price: number
  type: GridLevelType
  distanceFromCurrent: number
}

// =============================================================================
// Component Props
// =============================================================================

export interface StrategyProps {
  /** The strategy configuration and current state */
  strategy: Strategy
  /** Current market data for calculations and previews */
  currentMarket: CurrentMarket
  /** Calculated risk summary based on current settings */
  riskSummary: RiskSummary
  /** Preview of grid levels based on current settings */
  gridPreview: GridLevel[]
  /** Called when user wants to start the strategy */
  onStart?: () => void
  /** Called when user wants to pause the strategy */
  onPause?: () => void
  /** Called when user wants to stop the strategy */
  onStop?: () => void
  /** Called when user wants to resume a paused strategy */
  onResume?: () => void
  /** Called when user updates risk parameters */
  onUpdateRiskParameters?: (params: RiskParameters) => void
  /** Called when user updates grid settings */
  onUpdateGridSettings?: (settings: GridSettings) => void
  /** Called when user updates MACD filter settings */
  onUpdateMACDFilter?: (filter: MACDFilter) => void
  /** Called when user updates advanced settings */
  onUpdateAdvancedSettings?: (settings: AdvancedSettings) => void
  /** Called when user saves all changes */
  onSave?: () => void
}
