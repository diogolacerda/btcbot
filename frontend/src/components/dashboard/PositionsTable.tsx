/**
 * Positions Table Component
 *
 * Displays filled orders (open positions) awaiting take-profit.
 * Shows entry price, current price, unrealized P&L, and TP target.
 */

import type { OrderSchema } from '@/types/api'

interface PositionsTableProps {
  positions: OrderSchema[] | undefined
  currentPrice: number | undefined
  isLoading: boolean
  isError: boolean
  onPositionClick?: (position: OrderSchema) => void
}

function formatPrice(price: number): string {
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatPnL(pnl: number): string {
  const sign = pnl >= 0 ? '+' : ''
  return `${sign}$${pnl.toFixed(2)}`
}

function formatPercent(percent: number): string {
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

function calculateUnrealizedPnL(position: OrderSchema, currentPrice: number): { pnl: number; percent: number } {
  const entryValue = position.price * position.quantity
  const currentValue = currentPrice * position.quantity

  // For LONG positions: profit when price goes up
  // For SHORT positions: profit when price goes down
  const pnl = position.side === 'LONG'
    ? currentValue - entryValue
    : entryValue - currentValue

  const percent = (pnl / entryValue) * 100

  return { pnl, percent }
}

function calculateDistanceToTP(position: OrderSchema, currentPrice: number): number {
  const distancePercent = ((position.tpPrice - currentPrice) / currentPrice) * 100
  return position.side === 'LONG' ? distancePercent : -distancePercent
}

export function PositionsTable({
  positions,
  currentPrice,
  isLoading,
  isError,
  onPositionClick,
}: PositionsTableProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="h-6 w-40 bg-muted rounded animate-pulse" />
        </div>
        <div className="p-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Open Positions</h3>
        <p className="text-destructive text-sm">Failed to load positions</p>
      </div>
    )
  }

  const filledPositions = positions?.filter(p => p.status === 'FILLED') ?? []

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Open Positions</h3>
        <span className="text-sm text-muted-foreground">
          {filledPositions.length} {filledPositions.length === 1 ? 'position' : 'positions'}
        </span>
      </div>

      {filledPositions.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-muted-foreground">No open positions</p>
          <p className="text-sm text-muted-foreground mt-1">Positions appear when orders are filled</p>
        </div>
      ) : (
        <div className="divide-y divide-border">
          {filledPositions.map((position) => {
            const { pnl, percent } = currentPrice
              ? calculateUnrealizedPnL(position, currentPrice)
              : { pnl: 0, percent: 0 }
            const distanceToTP = currentPrice
              ? calculateDistanceToTP(position, currentPrice)
              : 0
            const isProfitable = pnl >= 0

            return (
              <div
                key={position.orderId}
                onClick={() => onPositionClick?.(position)}
                className={`p-4 hover:bg-muted/30 transition-colors ${onPositionClick ? 'cursor-pointer' : ''}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${position.side === 'LONG' ? 'text-green-500' : 'text-red-500'}`}>
                      {position.side}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {position.quantity.toFixed(4)} BTC
                    </span>
                  </div>
                  <div className="text-right">
                    <span className={`text-lg font-mono font-semibold ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
                      {formatPnL(pnl)}
                    </span>
                    <span className={`ml-2 text-sm ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
                      ({formatPercent(percent)})
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Entry</p>
                    <p className="font-mono text-foreground">{formatPrice(position.price)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Current</p>
                    <p className="font-mono text-foreground">{currentPrice ? formatPrice(currentPrice) : '--'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">TP Target</p>
                    <p className="font-mono text-foreground">
                      {formatPrice(position.tpPrice)}
                      <span className="text-xs text-muted-foreground ml-1">
                        ({formatPercent(distanceToTP)})
                      </span>
                    </p>
                  </div>
                </div>

                {/* Progress to TP */}
                {currentPrice && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Entry</span>
                      <span>TP</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${isProfitable ? 'bg-green-500' : 'bg-red-500'}`}
                        style={{
                          width: `${Math.min(100, Math.max(0, (1 - distanceToTP / (position.tpPrice - position.price) * currentPrice / 100) * 100))}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default PositionsTable
