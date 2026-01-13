// Core Data Model Types for Btcbot

export interface User {
  id: string
  name: string
  email: string
  avatarUrl?: string
}

export interface Account {
  id: string
  exchange: string
  mode: 'demo' | 'live'
  apiKey: string
  apiSecretMasked: string
  connectionStatus: 'connected' | 'disconnected' | 'testing'
  isActive: boolean
  createdAt: string
  lastTestedAt: string
}

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

export interface Trade {
  id: string
  symbol: string
  entryPrice: number
  exitPrice: number
  size: number
  side: 'long' | 'short'
  profit: number
  profitPercentage: number
  entryTime: string
  exitTime: string
  duration: string
  status: 'closed'
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

export interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  size: number
  entryPrice: number
  currentPrice: number
  leverage: number
  marginMode: 'crossed' | 'isolated'
  unrealizedPnL: number
  unrealizedPnLPercentage: number
  liquidationPrice: number
  takeProfitPrice?: number
  stopLossPrice?: number
  openedAt: string
}
