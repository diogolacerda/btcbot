/**
 * Orders Table Component
 *
 * Displays active grid orders including pending limit orders and filled positions.
 * Shows order details like price, TP price, quantity, and status.
 */

import type { OrderSchema, OrdersListResponse } from '@/types/api'

interface OrdersTableProps {
  data: OrdersListResponse | undefined
  isLoading: boolean
  isError: boolean
  onOrderClick?: (order: OrderSchema) => void
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  PENDING: { label: 'Pending', color: 'text-yellow-500', bgColor: 'bg-yellow-500/10' },
  FILLED: { label: 'Filled', color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  TP_HIT: { label: 'TP Hit', color: 'text-green-500', bgColor: 'bg-green-500/10' },
  CANCELLED: { label: 'Cancelled', color: 'text-gray-500', bgColor: 'bg-gray-500/10' },
}

function formatPrice(price: number): string {
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function OrdersTable({ data, isLoading, isError, onOrderClick }: OrdersTableProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="h-6 w-32 bg-muted rounded animate-pulse" />
        </div>
        <div className="p-4 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Orders</h3>
        <p className="text-destructive text-sm">Failed to load orders</p>
      </div>
    )
  }

  const orders = data?.orders ?? []

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Orders</h3>
        {data && (
          <div className="flex gap-4 text-sm">
            <span className="text-muted-foreground">
              Pending: <span className="text-yellow-500 font-medium">{data.pendingCount}</span>
            </span>
            <span className="text-muted-foreground">
              Filled: <span className="text-blue-500 font-medium">{data.filledCount}</span>
            </span>
          </div>
        )}
      </div>

      {orders.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-muted-foreground">No active orders</p>
          <p className="text-sm text-muted-foreground mt-1">Orders will appear when the bot is trading</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Side</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Price</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">TP Price</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Qty</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {orders.map((order) => {
                const statusConfig = STATUS_CONFIG[order.status] || STATUS_CONFIG.PENDING
                return (
                  <tr
                    key={order.orderId}
                    onClick={() => onOrderClick?.(order)}
                    className={`hover:bg-muted/30 transition-colors ${onOrderClick ? 'cursor-pointer' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <span className={`font-medium ${order.side === 'LONG' ? 'text-green-500' : 'text-red-500'}`}>
                        {order.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm text-foreground">{formatPrice(order.price)}</td>
                    <td className="px-4 py-3 font-mono text-sm text-foreground">{formatPrice(order.tpPrice)}</td>
                    <td className="px-4 py-3 font-mono text-sm text-foreground">{order.quantity.toFixed(4)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${statusConfig.color} ${statusConfig.bgColor}`}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{formatDate(order.createdAt)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > orders.length && (
        <div className="p-4 border-t border-border text-center">
          <span className="text-sm text-muted-foreground">
            Showing {orders.length} of {data.total} orders
          </span>
        </div>
      )}
    </div>
  )
}

export default OrdersTable
