/**
 * Strategy Edit Page (FE-STRAT-002, FE-STRAT-003)
 *
 * Page for editing an existing trading strategy.
 * Uses StrategyForm in edit mode with pre-populated values.
 * Includes MACDFilterSection for configuring MACD filter parameters.
 */

import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { StrategyForm, MACDFilterSection } from '@/components/Strategy'
import type { StrategyFormValues } from '@/components/Strategy'
import { useStrategy, useUpdateStrategy } from '@/hooks/useStrategies'

// ============================================================================
// Loading/Error States
// ============================================================================

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="h-4 w-32 bg-muted rounded animate-pulse mb-4" />
          <div className="h-8 w-64 bg-muted rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-muted rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-card border border-border rounded-lg p-6"
              >
                <div className="h-6 w-32 bg-muted rounded animate-pulse mb-4" />
                <div className="space-y-3">
                  <div className="h-10 bg-muted rounded animate-pulse" />
                  <div className="h-10 bg-muted rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-lg p-5 h-80 animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-card border border-destructive/50 rounded-lg p-8 text-center">
          <svg
            className="w-12 h-12 text-destructive mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Failed to Load Strategy
          </h2>
          <p className="text-muted-foreground mb-6">{message}</p>
          <button
            onClick={() => navigate('/strategies')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Back to Strategies
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function StrategyEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: strategy, isLoading, isError, error } = useStrategy(id || '')
  const updateMutation = useUpdateStrategy()

  const handleSubmit = async (data: StrategyFormValues) => {
    if (!id) return

    try {
      await updateMutation.mutateAsync({ id, data })
      toast.success('Strategy updated successfully')
      navigate('/strategies')
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to update strategy'
      toast.error(message)
      throw err // Re-throw to keep form in submitting state
    }
  }

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (isError || !strategy) {
    return (
      <ErrorState
        message={
          error instanceof Error
            ? error.message
            : 'Strategy not found or access denied'
        }
      />
    )
  }

  // Transform API response to form values
  const initialValues: Partial<StrategyFormValues> = {
    name: strategy.name,
    symbol: strategy.symbol,
    leverage: strategy.leverage,
    orderSizeUsdt: strategy.orderSizeUsdt,
    marginMode: strategy.marginMode,
    takeProfitPercent: strategy.takeProfitPercent,
    tpDynamicEnabled: strategy.tpDynamicEnabled,
    tpDynamicBase: strategy.tpDynamicBase,
    tpDynamicMin: strategy.tpDynamicMin,
    tpDynamicMax: strategy.tpDynamicMax,
    tpDynamicSafetyMargin: strategy.tpDynamicSafetyMargin,
    tpDynamicCheckInterval: strategy.tpDynamicCheckInterval,
    spacingType: strategy.spacingType,
    spacingValue: strategy.spacingValue,
    rangePercent: strategy.rangePercent,
    maxTotalOrders: strategy.maxTotalOrders,
    anchorMode: strategy.anchorMode,
    anchorThreshold: strategy.anchorThreshold,
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <a
              href="/strategies"
              className="hover:text-foreground transition-colors"
            >
              Strategies
            </a>
            <span>/</span>
            <span className="text-foreground">Edit</span>
          </nav>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-foreground">
              Edit Strategy
            </h1>
            {strategy.isActive && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-green-500/10 text-green-500">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                Active
              </span>
            )}
          </div>
          <p className="text-muted-foreground mt-2">
            Modify the configuration for &quot;{strategy.name}&quot;
          </p>
        </header>

        {/* Form with MACD Filter Section */}
        <StrategyForm
          mode="edit"
          initialValues={initialValues}
          onSubmit={handleSubmit}
          isSubmitting={updateMutation.isPending}
        >
          {/* MACD Filter Configuration (FE-STRAT-003) */}
          <MACDFilterSection strategyId={id!} />
        </StrategyForm>
      </div>
    </div>
  )
}
