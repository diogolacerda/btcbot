import { Play, Pause, Square, PlayCircle } from 'lucide-react'
import type { Strategy } from '@/../product/sections/strategy/types'

interface StrategyStatusCardProps {
  strategy: Strategy
  onStart?: () => void
  onPause?: () => void
  onStop?: () => void
  onResume?: () => void
}

export function StrategyStatusCard({
  strategy,
  onStart,
  onPause,
  onStop,
  onResume,
}: StrategyStatusCardProps) {
  const formatDate = (isoString: string) => {
    const now = new Date()
    const date = new Date(isoString)
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))

    if (diffHours > 0) {
      return `${diffHours}h ${diffMins}m ago`
    }
    return `${diffMins}m ago`
  }

  const formatDateTime = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const statusConfig = {
    active: {
      badge: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
      icon: '🟢',
    },
    paused: {
      badge: 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300',
      icon: '🟡',
    },
    stopped: {
      badge: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
      icon: '🔴',
    },
    wait: {
      badge: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
      icon: '⏳',
    },
  }

  const config = statusConfig[strategy.status]

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
            {strategy.name}
          </h2>
          <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${config.badge}`}
          >
            <span>{config.icon}</span>
            <span className="uppercase tracking-wide">{strategy.status}</span>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            {strategy.statusContext}
          </p>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2">
          {strategy.status === 'stopped' && (
            <button
              onClick={onStart}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
            >
              <Play className="w-4 h-4" />
              Start Strategy
            </button>
          )}

          {strategy.status === 'active' && (
            <>
              <button
                onClick={onPause}
                className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-medium"
              >
                <Pause className="w-4 h-4" />
                Pause
              </button>
              <button
                onClick={onStop}
                className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            </>
          )}

          {strategy.status === 'paused' && (
            <>
              <button
                onClick={onResume}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
              >
                <PlayCircle className="w-4 h-4" />
                Resume
              </button>
              <button
                onClick={onStop}
                className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            </>
          )}

          {strategy.status === 'wait' && (
            <button
              onClick={onStart}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
            >
              <Play className="w-4 h-4" />
              Start Strategy
            </button>
          )}
        </div>
      </div>

      {/* Cycle Info */}
      {strategy.status === 'active' && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Cycle Started</p>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {formatDate(strategy.cycle.startedAt)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">P&L Since Start</p>
            <p
              className={`text-sm font-mono font-bold ${
                strategy.cycle.pnlSinceStart > 0
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {strategy.cycle.pnlSinceStart > 0 ? '+' : ''}${strategy.cycle.pnlSinceStart.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Trades</p>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {strategy.cycle.tradesSinceStart}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Win Rate</p>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
              {strategy.cycle.winRateSinceStart}%
            </p>
          </div>
        </div>
      )}

      {/* Last Updated */}
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-4">
        Settings last changed: {formatDateTime(strategy.lastUpdated)}
      </p>
    </div>
  )
}
