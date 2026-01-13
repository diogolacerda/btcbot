import { ArrowUpDown, ArrowUp, ArrowDown, ExternalLink } from 'lucide-react'
import type { Trade, SortConfig, SortColumn } from '@/../product/sections/trade-history/types'

interface TradesTableProps {
  trades: Trade[]
  sortConfig?: SortConfig
  onSort?: (column: SortColumn) => void
  onViewDetails?: (tradeId: string) => void
}

export function TradesTable({ trades, sortConfig, onSort, onViewDetails }: TradesTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  const formatDateTime = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const getSortIcon = (column: SortColumn) => {
    if (sortConfig?.column !== column) {
      return <ArrowUpDown className="w-4 h-4 text-slate-400" />
    }
    return sortConfig.direction === 'asc' ? (
      <ArrowUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
    ) : (
      <ArrowDown className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
    )
  }

  const handleSort = (column: SortColumn) => {
    onSort?.(column)
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('closedAt')}
              >
                <div className="flex items-center gap-2">
                  Date/Time
                  {getSortIcon('closedAt')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('entryPrice')}
              >
                <div className="flex items-center gap-2">
                  Entry
                  {getSortIcon('entryPrice')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('exitPrice')}
              >
                <div className="flex items-center gap-2">
                  Exit
                  {getSortIcon('exitPrice')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('quantity')}
              >
                <div className="flex items-center gap-2">
                  Quantity
                  {getSortIcon('quantity')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('pnl')}
              >
                <div className="flex items-center gap-2">
                  P&L ($)
                  {getSortIcon('pnl')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('pnlPercent')}
              >
                <div className="flex items-center gap-2">
                  P&L (%)
                  {getSortIcon('pnlPercent')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                onClick={() => handleSort('duration')}
              >
                <div className="flex items-center gap-2">
                  Duration
                  {getSortIcon('duration')}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {trades.map((trade) => {
              const isProfitable = trade.pnl > 0
              return (
                <tr
                  key={trade.id}
                  className="hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                    {formatDateTime(trade.closedAt)}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-slate-700 dark:text-slate-300">
                    {formatCurrency(trade.entryPrice)}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-slate-700 dark:text-slate-300">
                    {formatCurrency(trade.exitPrice)}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-slate-700 dark:text-slate-300">
                    {trade.quantity}
                  </td>
                  <td
                    className={`px-4 py-3 text-sm font-mono font-medium ${
                      isProfitable
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {isProfitable ? '+' : ''}
                    {formatCurrency(trade.pnl)}
                  </td>
                  <td
                    className={`px-4 py-3 text-sm font-mono font-medium ${
                      isProfitable
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {isProfitable ? '+' : ''}
                    {trade.pnlPercent.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                    {formatDuration(trade.duration)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        trade.status === 'CLOSED'
                          ? 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                          : 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                      }`}
                    >
                      {trade.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onViewDetails?.(trade.id)}
                      className="inline-flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
                    >
                      View
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden divide-y divide-slate-200 dark:divide-slate-700">
        {trades.map((trade) => {
          const isProfitable = trade.pnl > 0
          return (
            <div key={trade.id} className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    {formatDateTime(trade.closedAt)}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {trade.symbol} • {trade.side}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    trade.status === 'CLOSED'
                      ? 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                      : 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  }`}
                >
                  {trade.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Entry</p>
                  <p className="text-sm font-mono text-slate-700 dark:text-slate-300">
                    {formatCurrency(trade.entryPrice)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Exit</p>
                  <p className="text-sm font-mono text-slate-700 dark:text-slate-300">
                    {formatCurrency(trade.exitPrice)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">P&L</p>
                  <p
                    className={`text-sm font-mono font-medium ${
                      isProfitable
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {isProfitable ? '+' : ''}
                    {formatCurrency(trade.pnl)} ({isProfitable ? '+' : ''}
                    {trade.pnlPercent.toFixed(2)}%)
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Duration</p>
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    {formatDuration(trade.duration)}
                  </p>
                </div>
              </div>

              <button
                onClick={() => onViewDetails?.(trade.id)}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors text-sm font-medium"
              >
                View Details
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
