/**
 * Strategy Create Page (FE-STRAT-002)
 *
 * Page for creating a new trading strategy.
 * Uses StrategyForm in create mode.
 */

import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { StrategyForm } from '@/components/Strategy'
import type { StrategyFormValues } from '@/components/Strategy'
import { useCreateStrategy } from '@/hooks/useStrategies'

export function StrategyCreatePage() {
  const navigate = useNavigate()
  const createMutation = useCreateStrategy()

  const handleSubmit = async (data: StrategyFormValues) => {
    try {
      await createMutation.mutateAsync(data)
      toast.success('Strategy created successfully')
      navigate('/strategies')
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to create strategy'
      toast.error(message)
      throw error // Re-throw to keep form in submitting state
    }
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
            <span className="text-foreground">New Strategy</span>
          </nav>
          <h1 className="text-3xl font-bold text-foreground">
            Create New Strategy
          </h1>
          <p className="text-muted-foreground mt-2">
            Configure your trading strategy parameters including risk settings,
            take profit, and grid configuration.
          </p>
        </header>

        {/* Form */}
        <StrategyForm
          mode="create"
          onSubmit={handleSubmit}
          isSubmitting={createMutation.isPending}
        />
      </div>
    </div>
  )
}
