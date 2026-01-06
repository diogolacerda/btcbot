/**
 * Market Overview Card Component
 *
 * Displays market data including BTC price, 24h change, funding rate,
 * MACD indicator values, and grid range information.
 */

import type {
  PriceResponse,
  FundingRateResponse,
  MACDDataResponse,
  GridRangeResponse,
} from '@/types/api'

interface MarketOverviewCardProps {
  price: PriceResponse | undefined
  funding: FundingRateResponse | undefined
  macd: MACDDataResponse | undefined
  gridRange: GridRangeResponse | undefined
  isLoading: boolean
  isError: boolean
}

function formatNumber(num: number | null | undefined, decimals = 2): string {
  if (num == null) return '--'
  return num.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function formatPercent(num: number | null | undefined): string {
  if (num == null) return '--'
  const sign = num >= 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

function formatCurrency(num: number | null | undefined): string {
  if (num == null) return '--'
  return `$${formatNumber(num)}`
}

const SIGNAL_CONFIG: Record<string, { label: string; color: string }> = {
  bullish: { label: 'Bullish', color: 'text-green-500' },
  bearish: { label: 'Bearish', color: 'text-red-500' },
  neutral: { label: 'Neutral', color: 'text-gray-500' },
}

export function MarketOverviewCard({
  price,
  funding,
  macd,
  gridRange,
  isLoading,
  isError,
}: MarketOverviewCardProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 animate-pulse">
        <div className="h-6 w-40 bg-muted rounded mb-4" />
        <div className="space-y-4">
          <div className="h-12 w-full bg-muted rounded" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-16 bg-muted rounded" />
            <div className="h-16 bg-muted rounded" />
            <div className="h-16 bg-muted rounded" />
            <div className="h-16 bg-muted rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Market Overview</h3>
        <p className="text-destructive text-sm">Failed to load market data</p>
      </div>
    )
  }

  const priceChange = price?.change24hPercent ?? 0
  const isPriceUp = priceChange >= 0
  const signalConfig = SIGNAL_CONFIG[macd?.signal ?? 'neutral']

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">Market Overview</h3>

      {/* Price Header */}
      <div className="mb-6">
        <div className="flex items-baseline gap-3">
          <span className="text-3xl font-mono font-bold text-foreground">
            {price ? formatCurrency(price.price) : '--'}
          </span>
          <span className={`text-lg font-medium ${isPriceUp ? 'text-green-500' : 'text-red-500'}`}>
            {price ? formatPercent(priceChange) : '--'}
          </span>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          24h Range: {price ? `${formatCurrency(price.low24h)} - ${formatCurrency(price.high24h)}` : '--'}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Funding Rate */}
        <div className="bg-muted/50 rounded-lg p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Funding Rate</p>
          <p className={`text-lg font-mono font-semibold ${(funding?.fundingRatePercent ?? 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {funding ? formatPercent(funding.fundingRatePercent) : '--'}
          </p>
          {funding && (
            <p className="text-xs text-muted-foreground mt-1">
              Next: {new Date(funding.nextFundingTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          )}
        </div>

        {/* MACD Signal */}
        <div className="bg-muted/50 rounded-lg p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">MACD Signal</p>
          <p className={`text-lg font-semibold ${signalConfig.color}`}>
            {signalConfig.label}
          </p>
          {macd && (
            <p className="text-xs text-muted-foreground mt-1">
              Histogram: {macd.histogramRising ? '↑ Rising' : '↓ Falling'}
            </p>
          )}
        </div>

        {/* MACD Values */}
        <div className="bg-muted/50 rounded-lg p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">MACD Line / Signal</p>
          <div className="flex gap-2 text-sm font-mono">
            <span className={macd && macd.macdLine >= 0 ? 'text-green-500' : 'text-red-500'}>
              {macd ? macd.macdLine.toFixed(2) : '--'}
            </span>
            <span className="text-muted-foreground">/</span>
            <span className={macd && macd.signalLine >= 0 ? 'text-green-500' : 'text-red-500'}>
              {macd ? macd.signalLine.toFixed(2) : '--'}
            </span>
          </div>
        </div>

        {/* Grid Position */}
        <div className="bg-muted/50 rounded-lg p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Grid Position</p>
          <p className="text-lg font-mono font-semibold text-foreground">
            {gridRange ? `${gridRange.pricePositionPercent.toFixed(0)}%` : '--'}
          </p>
          {gridRange && (
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(gridRange.gridLow)} - {formatCurrency(gridRange.gridHigh)}
            </p>
          )}
        </div>
      </div>

      {/* Volume */}
      {price && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">24h Volume</span>
            <span className="font-mono text-foreground">
              ${(price.volume24h / 1_000_000).toFixed(2)}M
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default MarketOverviewCard
