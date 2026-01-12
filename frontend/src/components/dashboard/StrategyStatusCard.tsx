/**
 * Strategy Status Card Component (FE-DASH-006)
 *
 * Displays current strategy status including state, strategy parameters, and order statistics.
 * Includes controls to activate/deactivate/pause/resume the strategy.
 *
 * Replaces BotStatusCard with strategy-centric view.
 */

import type { BotStatusResponse } from '@/types/api'

export interface StrategyStatusCardProps {
  data: BotStatusResponse | undefined
  strategyName?: string
  strategyTimeframe?: string
  strategySymbol?: string
  strategyLeverage?: number
  strategyOrderSize?: number
  strategyTakeProfit?: number
  isLoading: boolean
  isError: boolean
  onActivate?: () => void
  onDeactivate?: () => void
  onPause?: () => void
  onResume?: () => void
  isControlLoading?: boolean
}

const STATE_CONFIG: Record<
  string,
  { label: string; color: string; bgColor: string }
> = {
  INACTIVE: { label: 'Inactive', color: 'text-gray-500', bgColor: 'bg-gray-500/10' },
  WAIT: { label: 'Waiting', color: 'text-yellow-500', bgColor: 'bg-yellow-500/10' },
  ACTIVATE: { label: 'Activating', color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  ACTIVE: { label: 'Active', color: 'text-green-500', bgColor: 'bg-green-500/10' },
  PAUSE: { label: 'Paused', color: 'text-orange-500', bgColor: 'bg-orange-500/10' },
}

export function StrategyStatusCard({
  data,
  strategyName = 'Default Strategy',
  strategyTimeframe = '5m',
  strategySymbol = 'BTC-USDT',
  strategyLeverage = 10,
  strategyOrderSize = 100,
  strategyTakeProfit = 0.5,
  isLoading,
  isError,
  onActivate,
  onDeactivate,
  onPause,
  onResume,
  isControlLoading = false,
}: StrategyStatusCardProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 animate-pulse">
        <div className="h-6 w-40 bg-muted rounded mb-4" />
        <div className="space-y-3">
          <div className="h-4 w-full bg-muted rounded" />
          <div className="h-4 w-3/4 bg-muted rounded" />
          <div className="h-4 w-1/2 bg-muted rounded" />
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Strategy Status</h3>
        <p className="text-destructive text-sm">Failed to load strategy status</p>
      </div>
    )
  }

  const stateConfig = STATE_CONFIG[data.state] || STATE_CONFIG.INACTIVE
  const isRunning = data.isRunning
  const isPaused = data.state === 'PAUSE'

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      {/* Header with Title and State Badge */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Strategy Status</h3>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${stateConfig.color} ${stateConfig.bgColor}`}>
          {stateConfig.label}
        </div>
      </div>

      {/* Strategy Name */}
      <div className="mb-4">
        <p className="text-base font-medium text-foreground">{strategyName}</p>
        <p className="text-sm text-muted-foreground">{data.stateDescription}</p>
      </div>

      {/* Strategy Parameters Grid */}
      <div className="grid grid-cols-3 gap-3 mb-4 p-3 bg-muted/30 rounded-lg">
        <div className="text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Timeframe</p>
          <p className="text-sm font-semibold text-foreground">{strategyTimeframe}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Symbol</p>
          <p className="text-sm font-semibold text-foreground">{strategySymbol}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Leverage</p>
          <p className="text-sm font-semibold text-foreground">{strategyLeverage}x</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Order Size</p>
          <p className="text-sm font-semibold text-foreground">${strategyOrderSize}</p>
        </div>
        <div className="text-center col-span-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Take Profit</p>
          <p className="text-sm font-semibold text-foreground">{strategyTakeProfit.toFixed(2)}%</p>
        </div>
      </div>

      {/* Operational Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Pending Orders</p>
          <p className="text-lg font-mono font-semibold text-foreground">{data.orders.pendingOrders}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Open Positions</p>
          <p className="text-lg font-mono font-semibold text-foreground">{data.orders.openPositions}</p>
        </div>
      </div>

      {/* Total P&L */}
      <div className="border-t border-border pt-4 mb-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">Total P&L</span>
          <span className={`text-xl font-mono font-bold ${data.orders.totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            ${data.orders.totalPnl.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Error Indicators */}
      {(data.errors.marginError || data.errors.rateLimited) && (
        <div className="flex gap-2 mb-4">
          {data.errors.marginError && (
            <span className="px-2 py-1 text-xs bg-destructive/10 text-destructive rounded">Margin Error</span>
          )}
          {data.errors.rateLimited && (
            <span className="px-2 py-1 text-xs bg-yellow-500/10 text-yellow-500 rounded">Rate Limited</span>
          )}
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex gap-2">
        {isRunning ? (
          <>
            {isPaused ? (
              <button
                onClick={onResume}
                disabled={isControlLoading}
                title="Resume normal strategy operations and continue placing orders"
                className="flex-1 px-4 py-2 text-sm font-medium bg-green-500/10 text-green-600 rounded-md hover:bg-green-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Resume
              </button>
            ) : (
              <button
                onClick={onPause}
                disabled={isControlLoading}
                title="Stop creating new orders while keeping existing orders and positions active"
                className="flex-1 px-4 py-2 text-sm font-medium bg-yellow-500/10 text-yellow-600 rounded-md hover:bg-yellow-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Pause New Orders
              </button>
            )}
            <button
              onClick={onDeactivate}
              disabled={isControlLoading}
              title="Stop the bot completely and cancel all pending grid orders (TP orders will be preserved)"
              className="flex-1 px-4 py-2 text-sm font-medium bg-destructive/10 text-destructive rounded-md hover:bg-destructive/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Stop & Cancel Grid
            </button>
          </>
        ) : (
          <button
            onClick={onActivate}
            disabled={isControlLoading}
            className="flex-1 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Activate Strategy
          </button>
        )}
      </div>
    </div>
  )
}

export default StrategyStatusCard
