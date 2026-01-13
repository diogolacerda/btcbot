import { CheckCircle, XCircle, Pause, TrendingUp, Play } from 'lucide-react'
import type { ActivityEvent } from '@/../product/sections/dashboard/types'

interface ActivityFeedProps {
  activityEvents: ActivityEvent[]
}

const eventIcons = {
  ORDER_FILLED: CheckCircle,
  TRADE_CLOSED: TrendingUp,
  STRATEGY_PAUSED: Pause,
  TP_ADJUSTED: TrendingUp,
  CYCLE_ACTIVATED: Play,
}

const eventColors = {
  ORDER_FILLED: 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-950',
  TRADE_CLOSED: 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950',
  STRATEGY_PAUSED: 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-950',
  TP_ADJUSTED: 'text-violet-600 dark:text-violet-400 bg-violet-100 dark:bg-violet-950',
  CYCLE_ACTIVATED: 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-950',
}

export function ActivityFeed({ activityEvents }: ActivityFeedProps) {
  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    const seconds = Math.floor(diff / 1000)
    if (seconds < 60) return `${seconds}s ago`

    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`

    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`

    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-4">
        Recent Activity
      </h3>

      <div className="space-y-3">
        {activityEvents.length === 0 ? (
          <p className="text-center py-8 text-slate-500 dark:text-slate-400">
            No recent activity
          </p>
        ) : (
          activityEvents.map((event, index) => {
            const Icon = eventIcons[event.type]
            const colorClass = eventColors[event.type]

            return (
              <div
                key={event.id}
                className="flex items-start gap-3 pb-3 border-b border-slate-100 dark:border-slate-700 last:border-0 last:pb-0"
              >
                <div className={`p-2 rounded-lg ${colorClass}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-900 dark:text-slate-100">
                    {event.description}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {formatTimestamp(event.timestamp)}
                  </p>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
