import type { CumulativePnlDataPoint } from '@/../product/sections/trade-history/types'

interface PnlChartProps {
  cumulativePnlData: CumulativePnlDataPoint[]
}

export function PnlChart({ cumulativePnlData }: PnlChartProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  const maxPnl = Math.max(...cumulativePnlData.map((d) => d.cumulativePnl))
  const minPnl = Math.min(...cumulativePnlData.map((d) => d.cumulativePnl))
  const range = maxPnl - minPnl

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-4">
        Cumulative P&L
      </h3>

      {/* Simple bar chart visualization */}
      <div className="space-y-2">
        {cumulativePnlData.map((point, index) => {
          const percentage = range > 0 ? ((point.cumulativePnl - minPnl) / range) * 100 : 50
          const isPositive = point.cumulativePnl > 0

          return (
            <div key={point.date} className="flex items-center gap-3">
              <span className="text-xs text-slate-500 dark:text-slate-400 w-16">
                {formatDate(point.date)}
              </span>
              <div className="flex-1 h-8 bg-slate-100 dark:bg-slate-900 rounded overflow-hidden">
                <div
                  className={`h-full ${
                    isPositive
                      ? 'bg-emerald-500 dark:bg-emerald-600'
                      : 'bg-red-500 dark:bg-red-600'
                  } transition-all duration-300`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="text-sm font-mono text-slate-700 dark:text-slate-300 w-24 text-right">
                {formatCurrency(point.cumulativePnl)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
