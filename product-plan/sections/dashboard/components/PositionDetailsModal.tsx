import { X } from 'lucide-react'
import type { Position } from '@/../product/sections/dashboard/types'

interface PositionDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  position: Position | null
}

export function PositionDetailsModal({ isOpen, onClose, position }: PositionDetailsModalProps) {
  if (!isOpen || !position) return null

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price)
  }

  const formatDateTime = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const isProfitable = position.unrealizedPnl >= 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 max-w-lg w-full p-6">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        >
          <X className="w-5 h-5 text-slate-500 dark:text-slate-400" />
        </button>

        {/* Header */}
        <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-1">
          Position Details
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          Opened {formatDateTime(position.openedAt)}
        </p>

        {/* P&L Summary */}
        <div
          className={`p-4 rounded-lg mb-6 ${
            isProfitable
              ? 'bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800'
              : 'bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800'
          }`}
        >
          <p className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wide mb-1">
            Unrealized P&L
          </p>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-3xl font-bold font-mono ${
                isProfitable
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {isProfitable ? '+' : ''}
              {formatPrice(position.unrealizedPnl)}
            </span>
            <span
              className={`text-lg font-medium ${
                isProfitable
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              ({isProfitable ? '+' : ''}
              {position.pnlPercent.toFixed(2)}%)
            </span>
          </div>
        </div>

        {/* Details Grid */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Entry Price</p>
              <p className="text-lg font-bold font-mono text-slate-900 dark:text-slate-100">
                {formatPrice(position.entryPrice)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Current Price</p>
              <p className="text-lg font-bold font-mono text-slate-900 dark:text-slate-100">
                {formatPrice(position.currentPrice)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Quantity</p>
              <p className="text-lg font-bold font-mono text-slate-900 dark:text-slate-100">
                {position.quantity} BTC
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Side</p>
              <span className="inline-block px-2 py-1 rounded text-sm font-medium bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                {position.side}
              </span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Take Profit</p>
                <p className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  {formatPrice(position.takeProfitPrice)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Liquidation</p>
                <p className="text-lg font-bold font-mono text-red-600 dark:text-red-400">
                  {formatPrice(position.liquidationPrice)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
