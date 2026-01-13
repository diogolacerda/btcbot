import { Check, X, Loader2 } from 'lucide-react'
import type { Account } from '@/../product/sections/settings/types'

interface AccountCardProps {
  account: Account
  onTestConnection?: (id: string) => void
  onEdit?: (id: string) => void
  onSetActive?: (id: string) => void
  onRemove?: (id: string) => void
  isTestingConnection?: boolean
}

export function AccountCard({
  account,
  onTestConnection,
  onEdit,
  onSetActive,
  onRemove,
  isTestingConnection,
}: AccountCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div
      className={`relative p-6 bg-white dark:bg-slate-800 border rounded-lg transition-all ${
        account.isActive
          ? 'border-emerald-500 dark:border-emerald-400 ring-2 ring-emerald-500/20 dark:ring-emerald-400/20'
          : 'border-slate-200 dark:border-slate-700'
      }`}
    >
      {/* Active Badge */}
      {account.isActive && (
        <div className="absolute top-4 right-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 text-xs font-semibold rounded-full">
            <Check className="w-3 h-3" />
            Active
          </span>
        </div>
      )}

      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-2">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {account.exchange}
          </h3>
          <span
            className={`px-2.5 py-1 text-xs font-semibold rounded ${
              account.mode === 'demo'
                ? 'bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400'
                : 'bg-blue-100 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400'
            }`}
          >
            {account.mode === 'demo' ? 'Demo' : 'Live'}
          </span>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-2">
          {account.connectionStatus === 'connected' && (
            <>
              <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">
                Connected
              </span>
            </>
          )}
          {account.connectionStatus === 'disconnected' && (
            <>
              <X className="w-4 h-4 text-red-600 dark:text-red-400" />
              <span className="text-sm text-red-600 dark:text-red-400 font-medium">
                Disconnected
              </span>
            </>
          )}
          {account.connectionStatus === 'testing' && (
            <>
              <Loader2 className="w-4 h-4 text-slate-600 dark:text-slate-400 animate-spin" />
              <span className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                Testing...
              </span>
            </>
          )}
        </div>
      </div>

      {/* Details */}
      <div className="space-y-2 mb-4 text-sm">
        <div>
          <span className="text-slate-500 dark:text-slate-400">API Key:</span>{' '}
          <span className="font-mono text-slate-900 dark:text-slate-100">{account.apiKey}</span>
        </div>
        <div>
          <span className="text-slate-500 dark:text-slate-400">Created:</span>{' '}
          <span className="text-slate-900 dark:text-slate-100">{formatDate(account.createdAt)}</span>
        </div>
        <div>
          <span className="text-slate-500 dark:text-slate-400">Last Tested:</span>{' '}
          <span className="text-slate-900 dark:text-slate-100">
            {formatDate(account.lastTestedAt)}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onTestConnection?.(account.id)}
          disabled={isTestingConnection}
          className="px-3 py-1.5 text-sm font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 dark:hover:bg-emerald-950/50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isTestingConnection ? 'Testing...' : 'Test Connection'}
        </button>

        <button
          onClick={() => onEdit?.(account.id)}
          className="px-3 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded transition-colors"
        >
          Edit
        </button>

        {!account.isActive && (
          <button
            onClick={() => onSetActive?.(account.id)}
            className="px-3 py-1.5 text-sm font-medium text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 hover:bg-blue-100 dark:hover:bg-blue-950/50 rounded transition-colors"
          >
            Set Active
          </button>
        )}

        <button
          onClick={() => onRemove?.(account.id)}
          disabled={account.isActive}
          className="px-3 py-1.5 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/30 hover:bg-red-100 dark:hover:bg-red-950/50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title={account.isActive ? 'Cannot remove active account' : 'Remove account'}
        >
          Remove
        </button>
      </div>
    </div>
  )
}
