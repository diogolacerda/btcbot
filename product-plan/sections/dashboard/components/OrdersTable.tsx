import type { Order } from '@/../product/sections/dashboard/types'

interface OrdersTableProps {
  orders: Order[]
  onCancelOrder?: (orderId: string) => void
}

export function OrdersTable({ orders, onCancelOrder }: OrdersTableProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price)
  }

  const totalValue = orders.reduce((sum, order) => sum + order.price * order.quantity, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Active Orders
        </h4>
        <div className="text-sm">
          <span className="text-slate-500 dark:text-slate-400">{orders.length} orders • </span>
          <span className="text-slate-700 dark:text-slate-300 font-medium">
            Value: {formatPrice(totalValue)}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Price
              </th>
              <th className="text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Side
              </th>
              <th className="text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Quantity
              </th>
              <th className="text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Status
              </th>
              <th className="text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide pb-2">
                Action
              </th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-slate-500 dark:text-slate-400">
                  No active orders
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr
                  key={order.id}
                  className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors"
                >
                  <td className="py-3 text-sm font-mono text-slate-900 dark:text-slate-100">
                    {formatPrice(order.price)}
                  </td>
                  <td className="py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        order.side === 'BUY'
                          ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                          : 'bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300'
                      }`}
                    >
                      {order.side}
                    </span>
                  </td>
                  <td className="py-3 text-sm font-mono text-slate-900 dark:text-slate-100 text-right">
                    {order.quantity} BTC
                  </td>
                  <td className="py-3 text-sm text-slate-600 dark:text-slate-400">
                    {order.status}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => onCancelOrder?.(order.id)}
                      className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
                    >
                      Cancel
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
