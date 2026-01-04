// Core Data Model Types for Btcbot
// These types use camelCase (frontend convention) and will be transformed
// to/from snake_case when communicating with the backend API

export interface User {
  id: string
  email: string
  name: string | null
  isActive: boolean
  createdAt?: string
}

export interface Account {
  id: string
  userId: string
  exchange: string
  mode: 'demo' | 'live'
  apiKey: string
  apiSecretMasked: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface TradingConfig {
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

export interface GridConfig {
  id: string
  accountId: string
  gridSpacing: number
  maxTotalOrders: number
  gridAnchorMode: 'none' | 'hundred'
  createdAt: string
  updatedAt: string
}

export interface DynamicTPConfig {
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

export interface Position {
  symbol: string
  side: 'LONG' | 'SHORT'
  leverage: number
  entryPrice: number
  quantity: number
  tpPrice: number | null
  tpPercent: number | null
  unrealizedPnl: number | null
  openedAt: string
  gridLevel: number | null
}

export interface Trade {
  id: string
  accountId: string
  symbol: string
  side: 'LONG' | 'SHORT'
  leverage: number
  entryPrice: number
  exitPrice: number | null
  quantity: number
  tpPrice: number | null
  tpPercent: number | null
  pnl: number | null
  pnlPercent: number | null
  tradingFee: number
  fundingFee: number
  status: 'OPEN' | 'CLOSED' | 'CANCELLED'
  gridLevel: number | null
  openedAt: string
  filledAt: string | null
  closedAt: string | null
  createdAt: string
  updatedAt: string
}

export interface TradeStats {
  totalTrades: number
  openTrades: number
  closedTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  totalPnl: number
  totalFees: number
  netPnl: number
  avgPnlPerTrade: number
  avgWin: number
  avgLoss: number
  largestWin: number
  largestLoss: number
}

export interface BotStatus {
  state: 'INACTIVE' | 'WAIT' | 'ACTIVATE' | 'ACTIVE' | 'PAUSE'
  currentPrice: number
  macdTrend: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | null
  macdValue: number | null
  macdSignal: number | null
  macdHistogram: number | null
  openPositions: number
  pendingOrders: number
  totalPnl: number
  uptimeSeconds: number
}

// Strategy types for future use
export interface Strategy {
  id: string
  name: string
  status: 'active' | 'paused' | 'stopped' | 'wait'
  riskParameters: {
    positionSize: number
    maxTotalOrders: number
    leverage: number
    marginMode: 'crossed' | 'isolated'
  }
  gridSettings: {
    spacingType: 'fixed' | 'percentage'
    spacingValue: number
    gridRange: {
      min: number
      max: number
    }
    takeProfit: number
  }
  macdFilter: {
    enabled: boolean
    fastPeriod: number
    slowPeriod: number
    signalPeriod: number
    timeframe: '15m' | '1h' | '4h' | '1d'
  }
  advancedSettings: {
    dynamicTP: {
      enabled: boolean
      baseTP: number
      minTP: number
      maxTP: number
      safetyMargin: number
      checkInterval: number
    }
    autoReactivationMode: 'immediate' | 'full-cycle'
  }
  cycleStats?: {
    startTime: string
    runningTime: string
    profit: number
    trades: number
    winRate: number
  }
}

export interface Order {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  type: 'limit' | 'market'
  price: number
  size: number
  filledSize: number
  status: 'pending' | 'partial' | 'filled' | 'cancelled'
  createdAt: string
}
