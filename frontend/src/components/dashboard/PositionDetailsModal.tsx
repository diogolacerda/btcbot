/**
 * Position Details Modal Component
 *
 * Displays detailed information about a selected position/order.
 * Shows entry details, P&L calculations, and order history.
 */

import { useEffect, useRef } from 'react'
import type { OrderSchema } from '@/types/api'

interface PositionDetailsModalProps {
  position: OrderSchema | null
  currentPrice: number | undefined
  isOpen: boolean
  onClose: () => void
}

function formatPrice(price: number): string {
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function calculatePnL(position: OrderSchema, currentPrice: number): { pnl: number; percent: number } {
  const entryValue = position.price * position.quantity
  const currentValue = currentPrice * position.quantity

  const pnl = position.side === 'LONG'
    ? currentValue - entryValue
    : entryValue - currentValue

  const percent = (pnl / entryValue) * 100

  return { pnl, percent }
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pending',
  FILLED: 'Filled (Awaiting TP)',
  TP_HIT: 'Take Profit Hit',
  CANCELLED: 'Cancelled',
}

export function PositionDetailsModal({
  position,
  currentPrice,
  isOpen,
  onClose,
}: PositionDetailsModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Focus trap
  useEffect(() => {
    if (isOpen && modalRef.current) {
      modalRef.current.focus()
    }
  }, [isOpen])

  if (!isOpen || !position) return null

  const { pnl, percent } = currentPrice
    ? calculatePnL(position, currentPrice)
    : { pnl: 0, percent: 0 }
  const isProfitable = pnl >= 0
  const isFilled = position.status === 'FILLED'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="position-modal-title"
        tabIndex={-1}
        className="relative z-10 w-full max-w-lg mx-4 bg-card border border-border rounded-lg shadow-xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
          <div>
            <h2 id="position-modal-title" className="text-lg font-semibold text-foreground">
              Position Details
            </h2>
            <p className="text-sm text-muted-foreground">
              Order ID: <span className="font-mono">{position.orderId.slice(0, 12)}...</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-muted transition-colors"
          >
            <span className="text-muted-foreground text-xl">&times;</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Side & Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-xl font-bold ${position.side === 'LONG' ? 'text-green-500' : 'text-red-500'}`}>
                {position.side}
              </span>
              <span className="text-muted-foreground">
                {position.quantity.toFixed(4)} BTC
              </span>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              position.status === 'FILLED' ? 'bg-blue-500/10 text-blue-500' :
              position.status === 'TP_HIT' ? 'bg-green-500/10 text-green-500' :
              position.status === 'PENDING' ? 'bg-yellow-500/10 text-yellow-500' :
              'bg-gray-500/10 text-gray-500'
            }`}>
              {STATUS_LABELS[position.status]}
            </span>
          </div>

          {/* P&L (for filled positions) */}
          {isFilled && currentPrice && (
            <div className="bg-muted/50 rounded-lg p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Unrealized P&L</p>
              <div className="flex items-baseline gap-2">
                <span className={`text-2xl font-mono font-bold ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
                  {pnl >= 0 ? '+' : ''}${Math.abs(pnl).toFixed(2)}
                </span>
                <span className={`text-sm font-medium ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
                  ({percent >= 0 ? '+' : ''}{percent.toFixed(2)}%)
                </span>
              </div>
            </div>
          )}

          {/* Price Details */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-foreground">Price Information</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Entry Price</p>
                <p className="font-mono text-foreground">{formatPrice(position.price)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">TP Price</p>
                <p className="font-mono text-foreground">{formatPrice(position.tpPrice)}</p>
              </div>
              {currentPrice && (
                <>
                  <div>
                    <p className="text-xs text-muted-foreground">Current Price</p>
                    <p className="font-mono text-foreground">{formatPrice(currentPrice)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Distance to TP</p>
                    <p className="font-mono text-foreground">
                      {(((position.tpPrice - currentPrice) / currentPrice) * 100).toFixed(2)}%
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Value Calculation */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-foreground">Position Value</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Entry Value</p>
                <p className="font-mono text-foreground">{formatPrice(position.price * position.quantity)}</p>
              </div>
              {currentPrice && (
                <div>
                  <p className="text-xs text-muted-foreground">Current Value</p>
                  <p className="font-mono text-foreground">{formatPrice(currentPrice * position.quantity)}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-muted-foreground">TP Value</p>
                <p className="font-mono text-foreground">{formatPrice(position.tpPrice * position.quantity)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Expected Profit</p>
                <p className="font-mono text-green-500">
                  +${((position.tpPrice - position.price) * position.quantity).toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-foreground">Timeline</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created</span>
                <span className="text-foreground">{formatDate(position.createdAt)}</span>
              </div>
              {position.filledAt && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Filled</span>
                  <span className="text-foreground">{formatDate(position.filledAt)}</span>
                </div>
              )}
              {position.closedAt && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Closed</span>
                  <span className="text-foreground">{formatDate(position.closedAt)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Exchange IDs */}
          {position.exchangeTpOrderId && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-foreground">Exchange Reference</h4>
              <div className="text-xs font-mono bg-muted/50 rounded p-2 break-all text-muted-foreground">
                TP Order: {position.exchangeTpOrderId}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-card border-t border-border px-6 py-4">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-sm font-medium bg-muted text-foreground rounded-md hover:bg-accent transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default PositionDetailsModal
