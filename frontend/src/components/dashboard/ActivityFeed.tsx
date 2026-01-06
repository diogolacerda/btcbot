/**
 * Activity Feed Component
 *
 * Displays a chronological feed of trading activity events.
 * Includes order fills, trade closes, strategy changes, and errors.
 */

import type { ActivityEventSchema, EventTypeEnum } from '@/types/api'

interface ActivityFeedProps {
  events: ActivityEventSchema[] | undefined
  isLoading: boolean
  isError: boolean
  maxItems?: number
}

const EVENT_CONFIG: Record<EventTypeEnum, { icon: string; color: string; bgColor: string }> = {
  ORDER_FILLED: { icon: '📥', color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  TRADE_CLOSED: { icon: '💰', color: 'text-green-500', bgColor: 'bg-green-500/10' },
  STRATEGY_PAUSED: { icon: '⏸️', color: 'text-yellow-500', bgColor: 'bg-yellow-500/10' },
  STRATEGY_RESUMED: { icon: '▶️', color: 'text-green-500', bgColor: 'bg-green-500/10' },
  TP_ADJUSTED: { icon: '🎯', color: 'text-purple-500', bgColor: 'bg-purple-500/10' },
  CYCLE_ACTIVATED: { icon: '🔄', color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  CYCLE_DEACTIVATED: { icon: '⏹️', color: 'text-gray-500', bgColor: 'bg-gray-500/10' },
  BOT_STARTED: { icon: '🚀', color: 'text-green-500', bgColor: 'bg-green-500/10' },
  BOT_STOPPED: { icon: '🛑', color: 'text-red-500', bgColor: 'bg-red-500/10' },
  ERROR_OCCURRED: { icon: '⚠️', color: 'text-red-500', bgColor: 'bg-red-500/10' },
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function getEventLabel(eventType: EventTypeEnum): string {
  return eventType.split('_').map(word =>
    word.charAt(0) + word.slice(1).toLowerCase()
  ).join(' ')
}

export function ActivityFeed({ events, isLoading, isError, maxItems = 20 }: ActivityFeedProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="h-6 w-32 bg-muted rounded animate-pulse" />
        </div>
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex gap-3 animate-pulse">
              <div className="w-8 h-8 bg-muted rounded-full flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/4 bg-muted rounded" />
                <div className="h-3 w-1/4 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Activity Feed</h3>
        <p className="text-destructive text-sm">Failed to load activity</p>
      </div>
    )
  }

  const displayEvents = events?.slice(0, maxItems) ?? []

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground">Activity Feed</h3>
      </div>

      {displayEvents.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-muted-foreground">No recent activity</p>
          <p className="text-sm text-muted-foreground mt-1">Events will appear here as they occur</p>
        </div>
      ) : (
        <div className="divide-y divide-border max-h-96 overflow-y-auto">
          {displayEvents.map((event) => {
            const config = EVENT_CONFIG[event.eventType] || {
              icon: '📋',
              color: 'text-gray-500',
              bgColor: 'bg-gray-500/10'
            }

            return (
              <div key={event.id} className="p-4 hover:bg-muted/30 transition-colors">
                <div className="flex gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${config.bgColor}`}>
                    <span className="text-sm">{config.icon}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-sm font-medium ${config.color}`}>
                        {getEventLabel(event.eventType)}
                      </span>
                      <span className="text-xs text-muted-foreground flex-shrink-0">
                        {formatTimestamp(event.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm text-foreground mt-1 break-words">
                      {event.description}
                    </p>
                    {event.eventData && Object.keys(event.eventData).length > 0 && (
                      <div className="mt-2 text-xs text-muted-foreground font-mono bg-muted/50 rounded p-2">
                        {Object.entries(event.eventData).map(([key, value]) => (
                          <div key={key}>
                            <span className="text-muted-foreground">{key}:</span>{' '}
                            <span className="text-foreground">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {events && events.length > maxItems && (
        <div className="p-3 border-t border-border text-center">
          <span className="text-sm text-muted-foreground">
            Showing {maxItems} of {events.length} events
          </span>
        </div>
      )}
    </div>
  )
}

export default ActivityFeed
