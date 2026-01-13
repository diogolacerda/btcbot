/**
 * Performance Metrics Card Component
 *
 * Displays trading performance metrics including P&L, win rate,
 * trade counts, and best/worst trades for the selected period.
 */

import type { PerformanceMetricsResponse } from '@/types/api'

interface PerformanceMetricsCardProps {
  data: PerformanceMetricsResponse | undefined
  isLoading: boolean
  isError: boolean
}

function formatCurrency(num: number): string {
  const sign = num >= 0 ? '+' : ''
  return `${sign}$${Math.abs(num).toFixed(2)}`
}

function formatPercent(num: number): string {
  const sign = num >= 0 ? '+' : ''
  return `${sign}${num.toFixed(2)}%`
}

export function PerformanceMetricsCard({ data, isLoading, isError }: PerformanceMetricsCardProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 animate-pulse">
        <div className="h-6 w-48 bg-muted rounded mb-4" />
        <div className="space-y-4">
          <div className="h-16 w-full bg-muted rounded" />
          <div className="grid grid-cols-3 gap-4">
            <div className="h-12 bg-muted rounded" />
            <div className="h-12 bg-muted rounded" />
            <div className="h-12 bg-muted rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Performance Metrics</h3>
        <p className="text-destructive text-sm">Failed to load performance data</p>
      </div>
    )
  }

  // Empty state
  if (!data) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Performance Metrics</h3>
        <div className="text-center py-8">
          <p className="text-muted-foreground">No trading data available</p>
          <p className="text-sm text-muted-foreground mt-1">Start trading to see metrics</p>
        </div>
      </div>
    )
  }

  const { periodMetrics, totalMetrics } = data
  const isProfitable = periodMetrics.realizedPnl >= 0

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Performance Metrics</h3>
        <span className="text-sm text-muted-foreground capitalize">{periodMetrics.period}</span>
      </div>

      {/* Main P&L */}
      <div className="mb-6">
        <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Realized P&L</p>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-mono font-bold ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(periodMetrics.realizedPnl)}
          </span>
          <span className={`text-sm font-medium ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
            ({formatPercent(periodMetrics.pnlPercent)})
          </span>
        </div>
      </div>

      {/* Trade Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Trades</p>
          <p className="text-xl font-mono font-semibold text-foreground">{periodMetrics.tradesClosed}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Win Rate</p>
          <p className={`text-xl font-mono font-semibold ${periodMetrics.winRate >= 50 ? 'text-green-500' : 'text-red-500'}`}>
            {periodMetrics.winRate.toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">W/L</p>
          <p className="text-xl font-mono font-semibold text-foreground">
            <span className="text-green-500">{periodMetrics.winningTrades}</span>
            <span className="text-muted-foreground">/</span>
            <span className="text-red-500">{periodMetrics.losingTrades}</span>
          </p>
        </div>
      </div>

      {/* Total Stats */}
      <div className="border-t border-border pt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Total P&L (All Time)</span>
          <span className={`font-mono ${totalMetrics.totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(totalMetrics.totalPnl)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Avg Profit/Trade</span>
          <span className={`font-mono ${totalMetrics.avgProfitPerTrade >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(totalMetrics.avgProfitPerTrade)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Best Trade</span>
          <span className="font-mono text-green-500">{formatCurrency(totalMetrics.bestTrade)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Worst Trade</span>
          <span className={`font-mono ${totalMetrics.worstTrade < 0 ? 'text-red-500' : 'text-green-500'}`}>
            {formatCurrency(totalMetrics.worstTrade)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Total Fees</span>
          <span className="font-mono text-muted-foreground">-${totalMetrics.totalFees.toFixed(2)}</span>
        </div>
      </div>
    </div>
  )
}

export default PerformanceMetricsCard
