import type { PerformanceMetrics } from '@/../product/sections/dashboard/types'

interface PerformanceMetricsCardProps {
  performanceMetrics: PerformanceMetrics
}

export function PerformanceMetricsCard({ performanceMetrics }: PerformanceMetricsCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const isProfitable = (value: number) => value > 0

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-4">
        Performance Metrics
      </h3>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Today */}
        <div>
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
            Today
          </h4>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Realized P&L</p>
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-2xl font-bold font-mono ${
                    isProfitable(performanceMetrics.today.realizedPnl)
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatCurrency(performanceMetrics.today.realizedPnl)}
                </span>
                <span
                  className={`text-sm font-medium ${
                    isProfitable(performanceMetrics.today.pnlPercent)
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  ({formatPercent(performanceMetrics.today.pnlPercent)})
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Trades Closed</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {performanceMetrics.today.tradesClosed}
              </p>
            </div>
          </div>
        </div>

        {/* Total */}
        <div className="border-t md:border-t-0 md:border-l border-slate-200 dark:border-slate-700 pt-6 md:pt-0 md:pl-6">
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
            All Time
          </h4>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Total P&L</p>
              <p
                className={`text-2xl font-bold font-mono ${
                  isProfitable(performanceMetrics.total.totalPnl)
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {formatCurrency(performanceMetrics.total.totalPnl)}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Total Trades</p>
                <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  {performanceMetrics.total.totalTrades}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Avg/Trade</p>
                <p className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono">
                  {formatCurrency(performanceMetrics.total.avgProfitPerTrade)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
