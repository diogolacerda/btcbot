/**
 * Mock Data for Dashboard Tests
 *
 * Provides consistent mock data for testing dashboard components.
 */

import type {
  BotStatusResponse,
  PriceResponse,
  FundingRateResponse,
  MACDDataResponse,
  GridRangeResponse,
  PerformanceMetricsResponse,
  OrderSchema,
  ActivityEventSchema,
} from '@/types/api'
import type { Position } from '@/types'

// Bot Status Mock
export const mockBotStatus: BotStatusResponse = {
  status: 'running',
  state: 'ACTIVE',
  stateDescription: 'Grid is active and placing orders',
  isRunning: true,
  cycleActivated: true,
  cycleActivatedAt: '2025-01-06T10:00:00Z',
  lastUpdate: '2025-01-06T12:00:00Z',
  currentPrice: 98500.25,
  macd: {
    macdLine: 125.5,
    histogram: 45.2,
  },
  orders: {
    pendingOrders: 5,
    openPositions: 3,
    totalTrades: 150,
    totalPnl: 1250.75,
  },
  errors: {
    marginError: false,
    rateLimited: false,
  },
}

export const mockBotStatusStopped: BotStatusResponse = {
  ...mockBotStatus,
  status: 'stopped',
  state: 'INACTIVE',
  stateDescription: 'Bot is stopped',
  isRunning: false,
  cycleActivated: false,
  cycleActivatedAt: null,
}

// Market Data Mocks
export const mockPrice: PriceResponse = {
  symbol: 'BTC-USDT',
  price: 98500.25,
  change24h: 1250.50,
  change24hPercent: 1.28,
  high24h: 99000.00,
  low24h: 97000.00,
  volume24h: 15000000000,
  timestamp: '2025-01-06T12:00:00Z',
}

export const mockPriceNegative: PriceResponse = {
  ...mockPrice,
  change24h: -1500.75,
  change24hPercent: -1.52,
}

export const mockFundingRate: FundingRateResponse = {
  symbol: 'BTC-USDT',
  fundingRate: 0.0001,
  fundingRatePercent: 0.01,
  nextFundingTime: '2025-01-06T16:00:00Z',
  fundingIntervalHours: 8,
  markPrice: 98502.30,
  timestamp: '2025-01-06T12:00:00Z',
}

export const mockMacdData: MACDDataResponse = {
  symbol: 'BTC-USDT',
  macdLine: 125.5,
  signalLine: 80.3,
  histogram: 45.2,
  signal: 'bullish',
  histogramRising: true,
  bothLinesNegative: false,
  timeframe: '5m',
  timestamp: '2025-01-06T12:00:00Z',
}

export const mockMacdDataBearish: MACDDataResponse = {
  ...mockMacdData,
  macdLine: -150.0,
  signalLine: -100.0,
  histogram: -50.0,
  signal: 'bearish',
  histogramRising: false,
  bothLinesNegative: true,
}

export const mockGridRange: GridRangeResponse = {
  symbol: 'BTC-USDT',
  currentPrice: 98500.25,
  gridLow: 97000.00,
  gridHigh: 100000.00,
  rangePercent: 3.09,
  pricePositionPercent: 50.0,
  levelsPossible: 10,
  timestamp: '2025-01-06T12:00:00Z',
}

// Performance Metrics Mock
export const mockPerformanceMetrics: PerformanceMetricsResponse = {
  periodMetrics: {
    period: '7days',
    startDate: '2024-12-30T00:00:00Z',
    endDate: '2025-01-06T23:59:59Z',
    realizedPnl: 850.25,
    pnlPercent: 8.5,
    tradesClosed: 45,
    winningTrades: 38,
    losingTrades: 7,
    winRate: 84.4,
  },
  totalMetrics: {
    totalPnl: 12500.75,
    totalTrades: 450,
    avgProfitPerTrade: 27.78,
    totalFees: 125.50,
    netPnl: 12375.25,
    bestTrade: 125.50,
    worstTrade: -35.25,
  },
}

// Orders Mock
export const mockOrders: OrderSchema[] = [
  {
    orderId: 'order-1',
    price: 98000.00,
    tpPrice: 98500.00,
    quantity: 0.001,
    side: 'LONG',
    status: 'PENDING',
    createdAt: '2025-01-06T10:00:00Z',
    filledAt: null,
    closedAt: null,
    exchangeTpOrderId: null,
  },
  {
    orderId: 'order-2',
    price: 97500.00,
    tpPrice: 98000.00,
    quantity: 0.001,
    side: 'LONG',
    status: 'FILLED',
    createdAt: '2025-01-06T09:00:00Z',
    filledAt: '2025-01-06T09:30:00Z',
    closedAt: null,
    exchangeTpOrderId: 'tp-123',
  },
  {
    orderId: 'order-3',
    price: 96500.00,
    tpPrice: 97000.00,
    quantity: 0.001,
    side: 'LONG',
    status: 'TP_HIT',
    createdAt: '2025-01-06T08:00:00Z',
    filledAt: '2025-01-06T08:30:00Z',
    closedAt: '2025-01-06T09:00:00Z',
    exchangeTpOrderId: 'tp-122',
  },
]

// Positions Mock (from /trading/positions endpoint)
export const mockPositions: Position[] = [
  {
    symbol: 'BTC-USDT',
    side: 'LONG',
    leverage: 10,
    entryPrice: 97500.00,
    quantity: 0.001,
    tpPrice: 98000.00,
    tpPercent: 0.5,
    unrealizedPnl: 0.50,
    openedAt: '2025-01-06T09:30:00Z',
    gridLevel: 1,
  },
  {
    symbol: 'BTC-USDT',
    side: 'LONG',
    leverage: 10,
    entryPrice: 98200.00,
    quantity: 0.002,
    tpPrice: 98700.00,
    tpPercent: 0.5,
    unrealizedPnl: -0.40,
    openedAt: '2025-01-06T10:15:00Z',
    gridLevel: 2,
  },
]

// Activity Events Mock
export const mockActivityEvents: ActivityEventSchema[] = [
  {
    id: 'event-1',
    eventType: 'ORDER_FILLED',
    description: 'Order filled at $98,000.00',
    eventData: { price: 98000.00, side: 'LONG' },
    timestamp: '2025-01-06T11:30:00Z',
  },
  {
    id: 'event-2',
    eventType: 'TRADE_CLOSED',
    description: 'Trade closed with +$25.50 profit',
    eventData: { pnl: 25.50, entryPrice: 97000.00, exitPrice: 97500.00 },
    timestamp: '2025-01-06T11:00:00Z',
  },
  {
    id: 'event-3',
    eventType: 'CYCLE_ACTIVATED',
    description: 'Trading cycle activated',
    eventData: null,
    timestamp: '2025-01-06T10:00:00Z',
  },
  {
    id: 'event-4',
    eventType: 'BOT_STARTED',
    description: 'Bot started',
    eventData: null,
    timestamp: '2025-01-06T09:00:00Z',
  },
  {
    id: 'event-5',
    eventType: 'ERROR_OCCURRED',
    description: 'Rate limit exceeded, waiting...',
    eventData: { errorCode: 'RATE_LIMIT' },
    timestamp: '2025-01-06T08:00:00Z',
  },
]
