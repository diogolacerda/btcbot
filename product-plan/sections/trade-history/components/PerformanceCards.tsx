import { TrendingUp, TrendingDown } from 'lucide-react'
import type { PerformanceMetrics } from '@/../product/sections/trade-history/types'

interface PerformanceCardsProps {
  performanceMetrics: PerformanceMetrics
}

export function PerformanceCards({ performanceMetrics }: PerformanceCardsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  const isProfitable = performanceMetrics.totalPnl > 0

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Total P&L */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
          Total P&L
        </p>
        <div className="flex items-baseline gap-2">
          <p
            className={`text-2xl font-bold font-mono ${
              isProfitable
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          >
            {formatCurrency(performanceMetrics.totalPnl)}
          </p>
          {isProfitable ? (
            <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />
          )}
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          +{performanceMetrics.roi}% ROI
        </p>
      </div>

      {/* Win Rate */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
          Win Rate
        </p>
        <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {performanceMetrics.winRate}%
        </p>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          {performanceMetrics.winningTrades} wins / {performanceMetrics.losingTrades} losses
        </p>
      </div>

      {/* Total Trades */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
          Total Trades
        </p>
        <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {performanceMetrics.totalTrades}
        </p>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          Avg: {formatCurrency(performanceMetrics.avgProfit)}
        </p>
      </div>

      {/* Best Trade */}
      <div className="bg-emerald-50 dark:bg-emerald-950/50 rounded-lg border border-emerald-200 dark:border-emerald-800 p-4">
        <p className="text-xs text-emerald-700 dark:text-emerald-400 uppercase tracking-wide mb-1">
          Best Trade
        </p>
        <p className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
          +{formatCurrency(performanceMetrics.bestTrade.pnl)}
        </p>
        <p className="text-sm text-emerald-700 dark:text-emerald-300 mt-1">
          {formatDate(performanceMetrics.bestTrade.date)}
        </p>
      </div>

      {/* Worst Trade */}
      <div className="bg-red-50 dark:bg-red-950/50 rounded-lg border border-red-200 dark:border-red-800 p-4">
        <p className="text-xs text-red-700 dark:text-red-400 uppercase tracking-wide mb-1">
          Worst Trade
        </p>
        <p className="text-2xl font-bold font-mono text-red-600 dark:text-red-400">
          {formatCurrency(performanceMetrics.worstTrade.pnl)}
        </p>
        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
          {formatDate(performanceMetrics.worstTrade.date)}
        </p>
      </div>

      {/* Average Profit */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
          Avg Profit/Trade
        </p>
        <p className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
          {formatCurrency(performanceMetrics.avgProfit)}
        </p>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Per closed trade</p>
      </div>
    </div>
  )
}
