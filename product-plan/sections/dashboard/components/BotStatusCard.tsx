import { Pause, Square, Play, Clock } from 'lucide-react'
import type { BotStatusData } from '@/../product/sections/dashboard/types'

interface BotStatusCardProps {
  botStatus: BotStatusData
  onPause?: () => void
  onStop?: () => void
  onResume?: () => void
  onStart?: () => void
}

export function BotStatusCard({
  botStatus,
  onPause,
  onStop,
  onResume,
  onStart,
}: BotStatusCardProps) {
  const statusConfig = {
    ACTIVE: {
      label: 'ACTIVE',
      color: 'emerald',
      icon: '🟢',
      actions: [
        { label: 'Pause', onClick: onPause, icon: Pause },
        { label: 'Stop', onClick: onStop, icon: Square, variant: 'danger' as const },
      ],
    },
    PAUSED: {
      label: 'PAUSED',
      color: 'amber',
      icon: '🟡',
      actions: [
        { label: 'Resume', onClick: onResume, icon: Play },
        { label: 'Stop', onClick: onStop, icon: Square, variant: 'danger' as const },
      ],
    },
    STOPPED: {
      label: 'STOPPED',
      color: 'red',
      icon: '🔴',
      actions: [{ label: 'Start', onClick: onStart, icon: Play }],
    },
    WAIT: {
      label: 'WAIT',
      color: 'slate',
      icon: '⏳',
      actions: [],
    },
  }

  const config = statusConfig[botStatus.status]

  const formatDuration = (isoString: string) => {
    const start = new Date(isoString)
    const now = new Date()
    const diff = now.getTime() - start.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return `${hours}h ${minutes}m ago`
  }

  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const seconds = Math.floor(diff / 1000)

    if (seconds < 60) return `${seconds} seconds ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes} minutes ago`
    const hours = Math.floor(minutes / 60)
    return `${hours} hours ago`
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`px-3 py-1 rounded-full text-sm font-bold bg-${config.color}-100 dark:bg-${config.color}-950 text-${config.color}-700 dark:text-${config.color}-300`}
            >
              {config.icon} {config.label}
            </span>
          </div>
          <p className="text-slate-700 dark:text-slate-300 font-medium mt-2">
            {botStatus.stateDescription}
          </p>
        </div>

        <div className="flex gap-2">
          {config.actions.map((action) => {
            const Icon = action.icon
            return (
              <button
                key={action.label}
                onClick={action.onClick}
                className={`p-2 rounded-lg transition-colors ${
                  action.variant === 'danger'
                    ? 'bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900'
                    : 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-200 dark:hover:bg-emerald-900'
                }`}
                title={action.label}
              >
                <Icon className="w-4 h-4" />
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-2 text-sm">
        {botStatus.status !== 'STOPPED' && botStatus.status !== 'WAIT' && (
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <Clock className="w-4 h-4" />
            <span>Cycle activated {formatDuration(botStatus.cycleActivatedAt)}</span>
          </div>
        )}
        <div className="text-slate-500 dark:text-slate-400">
          Last updated {formatTimestamp(botStatus.lastUpdate)}
        </div>
      </div>
    </div>
  )
}
