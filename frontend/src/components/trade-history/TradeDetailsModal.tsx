import { X, TrendingUp, TrendingDown } from 'lucide-react'
import { useEffect } from 'react'
import type { Trade } from './types'

interface TradeDetailsModalProps {
  trade: Trade | null
  onClose: () => void
}

export function TradeDetailsModal({ trade, onClose }: TradeDetailsModalProps) {
  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (trade) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [trade, onClose])

  if (!trade) return null

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
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  const isProfitable = trade.pnl > 0

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              Trade Details
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {trade.symbol} - {trade.side}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500 dark:text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Overview */}
          <div>
            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
              Overview
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Order ID</p>
                <p className="text-sm font-mono text-slate-700 dark:text-slate-300 mt-1">
                  {trade.orderId}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">TP Order ID</p>
                <p className="text-sm font-mono text-slate-700 dark:text-slate-300 mt-1">
                  {trade.tpOrderId}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Leverage</p>
                <p className="text-sm text-slate-700 dark:text-slate-300 mt-1">
                  {trade.leverage}x
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Status</p>
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-1 ${
                    trade.status === 'CLOSED'
                      ? 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                      : 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  }`}
                >
                  {trade.status}
                </span>
              </div>
            </div>
          </div>

          {/* Prices & P&L */}
          <div>
            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
              Prices & P&L
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Entry Price</p>
                <p className="text-lg font-mono text-slate-700 dark:text-slate-300 mt-1">
                  {formatCurrency(trade.entryPrice)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Exit Price</p>
                <p className="text-lg font-mono text-slate-700 dark:text-slate-300 mt-1">
                  {formatCurrency(trade.exitPrice)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Quantity</p>
                <p className="text-lg font-mono text-slate-700 dark:text-slate-300 mt-1">
                  {trade.quantity}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400">Gross P&L</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <p
                    className={`text-lg font-mono font-bold ${
                      isProfitable
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {isProfitable ? '+' : ''}
                    {formatCurrency(trade.pnl)}
                  </p>
                  {isProfitable ? (
                    <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />
                  )}
                </div>
                <p
                  className={`text-sm font-mono ${
                    isProfitable
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {isProfitable ? '+' : ''}
                  {trade.pnlPercent.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>

          {/* Fees */}
          <div>
            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
              Fees Breakdown
            </h3>
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Trading Fee
                </span>
                <span className="text-sm font-mono text-slate-700 dark:text-slate-300">
                  {formatCurrency(trade.fees.tradingFee)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Funding Fee
                </span>
                <span className="text-sm font-mono text-slate-700 dark:text-slate-300">
                  {formatCurrency(trade.fees.fundingFee)}
                </span>
              </div>
              <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Net P&L
                  </span>
                  <span
                    className={`text-sm font-mono font-bold ${
                      trade.fees.netPnl > 0
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {trade.fees.netPnl > 0 ? '+' : ''}
                    {formatCurrency(trade.fees.netPnl)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
              Timeline
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Opened</span>
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {formatDateTime(trade.openedAt)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Filled</span>
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {formatDateTime(trade.filledAt)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Closed</span>
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {formatDateTime(trade.closedAt)}
                </span>
              </div>
              <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Duration
                  </span>
                  <span className="text-sm font-mono text-slate-700 dark:text-slate-300">
                    {formatDuration(trade.duration)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* TP Adjustments */}
          {trade.tpAdjustments.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 uppercase tracking-wide mb-3">
                Take-Profit Adjustments
              </h3>
              <div className="space-y-2">
                {trade.tpAdjustments.map((adjustment, index) => (
                  <div
                    key={index}
                    className="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {formatDateTime(adjustment.timestamp)}
                      </span>
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                        {adjustment.oldTp}% → {adjustment.newTp}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {adjustment.reason}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-6 py-4">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
