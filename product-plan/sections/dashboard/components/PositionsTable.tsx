import type { Position } from '@/../product/sections/dashboard/types'

interface PositionsTableProps {
  positions: Position[]
  onViewPosition?: (positionId: string) => void
}

export function PositionsTable({ positions, onViewPosition }: PositionsTableProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price)
  }

  const formatPnl = (pnl: number, percent: number) => {
    const sign = pnl >= 0 ? '+' : ''
    return `${sign}${formatPrice(pnl)} (${sign}${percent.toFixed(2)}%)`
  }

  const totalUnrealizedPnl = positions.reduce((sum, pos) => sum + pos.unrealizedPnl, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Open Positions
        </h4>
        <div className="text-sm">
          <span className="text-slate-500 dark:text-slate-400">Unrealized P&L: </span>
          <span
            className={`font-bold font-mono ${
              totalUnrealizedPnl >= 0
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          >
            {formatPrice(totalUnrealizedPnl)}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Entry Price
              </th>
              <th className="text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Current Price
              </th>
              <th className="text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Quantity
              </th>
              <th className="text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                P&L
              </th>
              <th className="text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Action
              </th>
            </tr>
          </thead>
          <tbody>
            {positions.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-slate-500 dark:text-slate-400">
                  No open positions
                </td>
              </tr>
            ) : (
              positions.map((position) => (
                <tr
                  key={position.id}
                  className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors"
                >
                  <td className="py-3 text-sm font-mono text-slate-900 dark:text-slate-100">
                    {formatPrice(position.entryPrice)}
                  </td>
                  <td className="py-3 text-sm font-mono text-slate-900 dark:text-slate-100">
                    {formatPrice(position.currentPrice)}
                  </td>
                  <td className="py-3 text-sm font-mono text-slate-900 dark:text-slate-100 text-right">
                    {position.quantity} BTC
                  </td>
                  <td
                    className={`py-3 text-sm font-mono font-medium text-right ${
                      position.unrealizedPnl >= 0
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {formatPnl(position.unrealizedPnl, position.pnlPercent)}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => onViewPosition?.(position.id)}
                      className="text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 font-medium"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
