/**
 * Strategy List Page (FE-STRAT-001)
 *
 * Displays all strategies for the authenticated account.
 * Allows viewing, activating, editing, and deleting strategies.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  useStrategies,
  useActivateStrategy,
  useDeleteStrategy,
} from '@/hooks/useStrategies'
import { ConfirmDialog } from '@/components/dashboard/ConfirmDialog'
import type { StrategyResponse } from '@/types/api'

// ============================================================================
// Types
// ============================================================================

interface ActionDialogState {
  type: 'activate' | 'delete' | null
  strategy: StrategyResponse | null
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatCurrency(value: number): string {
  return `$${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// ============================================================================
// Sub-components
// ============================================================================

function LoadingSkeleton() {
  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border">
        <div className="h-6 w-32 bg-muted rounded animate-pulse" />
      </div>
      <div className="p-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-muted rounded animate-pulse" />
        ))}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="bg-card border border-border rounded-lg p-8 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary-100 dark:bg-secondary-900/20 mb-4">
        <svg
          className="w-8 h-8 text-secondary-600 dark:text-secondary-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-foreground mb-2">
        No Strategies Yet
      </h2>
      <p className="text-muted-foreground max-w-md mx-auto mb-6">
        Create your first trading strategy to start configuring grid levels,
        MACD parameters, and risk settings.
      </p>
      <Link
        to="/strategies/new"
        className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v16m8-8H4"
          />
        </svg>
        Create Strategy
      </Link>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-card border border-destructive/50 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-foreground mb-2">
        Failed to Load Strategies
      </h3>
      <p className="text-destructive text-sm">{message}</p>
    </div>
  )
}

function ActiveBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-green-500/10 text-green-500">
      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
      Active
    </span>
  )
}

interface StrategyRowProps {
  strategy: StrategyResponse
  onActivate: (strategy: StrategyResponse) => void
  onDelete: (strategy: StrategyResponse) => void
}

function StrategyRow({ strategy, onActivate, onDelete }: StrategyRowProps) {
  return (
    <tr className="hover:bg-muted/30 transition-colors">
      {/* Name */}
      <td className="px-4 py-4">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{strategy.name}</span>
          {strategy.isActive && <ActiveBadge />}
        </div>
      </td>

      {/* Symbol */}
      <td className="px-4 py-3 text-sm text-muted-foreground">
        {strategy.symbol}
      </td>

      {/* Leverage */}
      <td className="px-4 py-3 text-sm text-foreground">{strategy.leverage}x</td>

      {/* Position Size */}
      <td className="px-4 py-3 text-sm text-foreground">
        {formatCurrency(strategy.orderSizeUsdt)}
      </td>

      {/* Take Profit */}
      <td className="px-4 py-3 text-sm text-foreground">
        {strategy.takeProfitPercent}%
        {strategy.tpDynamicEnabled && (
          <span className="ml-1 text-xs text-muted-foreground">(dynamic)</span>
        )}
      </td>

      {/* Created */}
      <td className="px-4 py-3 text-sm text-muted-foreground">
        {formatDate(strategy.createdAt)}
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {/* Activate Button */}
          {!strategy.isActive && (
            <button
              onClick={() => onActivate(strategy)}
              className="p-1.5 text-green-500 hover:bg-green-500/10 rounded transition-colors"
              title="Activate Strategy"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </button>
          )}

          {/* Edit Button */}
          <Link
            to={`/strategies/${strategy.id}/edit`}
            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
            title="Edit Strategy"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </Link>

          {/* Delete Button */}
          <button
            onClick={() => onDelete(strategy)}
            className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors"
            title="Delete Strategy"
            disabled={strategy.isActive}
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </td>
    </tr>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function StrategyListPage() {
  const [actionDialog, setActionDialog] = useState<ActionDialogState>({
    type: null,
    strategy: null,
  })

  const { data: strategies, isLoading, isError, error } = useStrategies()
  const activateMutation = useActivateStrategy()
  const deleteMutation = useDeleteStrategy()

  const handleActivate = (strategy: StrategyResponse) => {
    setActionDialog({ type: 'activate', strategy })
  }

  const handleDelete = (strategy: StrategyResponse) => {
    if (strategy.isActive) return // Can't delete active strategy
    setActionDialog({ type: 'delete', strategy })
  }

  const handleConfirmAction = async () => {
    if (!actionDialog.strategy) return

    if (actionDialog.type === 'activate') {
      await activateMutation.mutateAsync(actionDialog.strategy.id)
    } else if (actionDialog.type === 'delete') {
      await deleteMutation.mutateAsync(actionDialog.strategy.id)
    }

    setActionDialog({ type: null, strategy: null })
  }

  const handleCancelAction = () => {
    setActionDialog({ type: null, strategy: null })
  }

  // Find current active strategy for the activation warning
  const activeStrategy = strategies?.find((s) => s.isActive)

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">
              Strategies
            </h1>
            <p className="text-muted-foreground">
              Manage your trading strategies and configurations
            </p>
          </div>
          <Link
            to="/strategies/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create Strategy
          </Link>
        </header>

        {/* Content */}
        {isLoading ? (
          <LoadingSkeleton />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'Unknown error'}
          />
        ) : !strategies || strategies.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Symbol
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Leverage
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Position Size
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Take Profit
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Created
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {strategies.map((strategy) => (
                    <StrategyRow
                      key={strategy.id}
                      strategy={strategy}
                      onActivate={handleActivate}
                      onDelete={handleDelete}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Confirm Dialogs */}
        <ConfirmDialog
          isOpen={actionDialog.type === 'activate'}
          title="Activate Strategy"
          message={
            activeStrategy
              ? `Activating "${actionDialog.strategy?.name}" will deactivate the current strategy "${activeStrategy.name}". Are you sure you want to continue?`
              : `Are you sure you want to activate "${actionDialog.strategy?.name}"?`
          }
          confirmLabel="Activate"
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
        />

        <ConfirmDialog
          isOpen={actionDialog.type === 'delete'}
          title="Delete Strategy"
          message={`Are you sure you want to delete "${actionDialog.strategy?.name}"? This action cannot be undone.`}
          confirmLabel="Delete"
          variant="danger"
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
        />
      </div>
    </div>
  )
}
