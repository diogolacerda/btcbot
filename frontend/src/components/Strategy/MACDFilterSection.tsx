/**
 * MACD Filter Configuration Section (FE-STRAT-003)
 *
 * Collapsible section for configuring MACD filter parameters.
 * Only shown in edit mode since the config is created with the strategy.
 */

import { useState, useMemo } from 'react'
import {
  useMACDFilterConfig,
  useUpdateMACDFilterConfig,
} from '@/hooks/useStrategies'
import type { MACDTimeframe } from '@/types/api'

// ============================================================================
// Constants
// ============================================================================

const TIMEFRAMES: { value: MACDTimeframe; label: string }[] = [
  { value: '1m', label: '1 minute' },
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '1d', label: '1 day' },
  { value: '1w', label: '1 week' },
]

const PERIOD_MIN = 1
const PERIOD_MAX = 100

// ============================================================================
// Types
// ============================================================================

interface MACDFilterSectionProps {
  strategyId: string
}

interface FormState {
  enabled: boolean
  fastPeriod: number
  slowPeriod: number
  signalPeriod: number
  timeframe: MACDTimeframe
}

// ============================================================================
// Component
// ============================================================================

export function MACDFilterSection({ strategyId }: MACDFilterSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [localChanges, setLocalChanges] = useState<Partial<FormState> | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: macdConfig, isLoading, isError } = useMACDFilterConfig(strategyId)
  const updateMutation = useUpdateMACDFilterConfig()

  // Derive form state from server data + local changes
  const formState: FormState = useMemo(() => {
    const serverState: FormState = macdConfig
      ? {
          enabled: macdConfig.enabled,
          fastPeriod: macdConfig.fastPeriod,
          slowPeriod: macdConfig.slowPeriod,
          signalPeriod: macdConfig.signalPeriod,
          timeframe: macdConfig.timeframe,
        }
      : {
          enabled: true,
          fastPeriod: 12,
          slowPeriod: 26,
          signalPeriod: 9,
          timeframe: '1h',
        }

    return localChanges ? { ...serverState, ...localChanges } : serverState
  }, [macdConfig, localChanges])

  const hasChanges = localChanges !== null

  // Validation
  const validate = (state: FormState): Record<string, string> => {
    const newErrors: Record<string, string> = {}

    if (state.fastPeriod < PERIOD_MIN || state.fastPeriod > PERIOD_MAX) {
      newErrors.fastPeriod = `Must be between ${PERIOD_MIN} and ${PERIOD_MAX}`
    }
    if (state.slowPeriod < PERIOD_MIN || state.slowPeriod > PERIOD_MAX) {
      newErrors.slowPeriod = `Must be between ${PERIOD_MIN} and ${PERIOD_MAX}`
    }
    if (state.signalPeriod < PERIOD_MIN || state.signalPeriod > PERIOD_MAX) {
      newErrors.signalPeriod = `Must be between ${PERIOD_MIN} and ${PERIOD_MAX}`
    }
    if (state.slowPeriod <= state.fastPeriod) {
      newErrors.slowPeriod = 'Slow period must be greater than fast period'
    }

    return newErrors
  }

  const handleChange = (field: keyof FormState, value: boolean | number | string) => {
    const newChanges = { ...localChanges, [field]: value }
    setLocalChanges(newChanges)

    // Compute new state for validation
    const serverState: FormState = macdConfig
      ? {
          enabled: macdConfig.enabled,
          fastPeriod: macdConfig.fastPeriod,
          slowPeriod: macdConfig.slowPeriod,
          signalPeriod: macdConfig.signalPeriod,
          timeframe: macdConfig.timeframe,
        }
      : {
          enabled: true,
          fastPeriod: 12,
          slowPeriod: 26,
          signalPeriod: 9,
          timeframe: '1h',
        }
    const newState = { ...serverState, ...newChanges }
    setErrors(validate(newState))
  }

  const handleSave = async () => {
    const validationErrors = validate(formState)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    try {
      await updateMutation.mutateAsync({
        strategyId,
        data: formState,
      })
      setLocalChanges(null)
    } catch {
      // Error is handled by mutation
    }
  }

  const handleReset = () => {
    setLocalChanges(null)
    setErrors({})
  }

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="animate-pulse flex items-center gap-2">
          <div className="h-5 w-5 bg-muted rounded" />
          <div className="h-5 w-32 bg-muted rounded" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <div className="flex items-center gap-2 text-destructive">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Failed to load MACD filter configuration</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      {/* Collapsible Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-2 h-2 rounded-full ${formState.enabled ? 'bg-green-500' : 'bg-muted-foreground'}`}
          />
          <div className="text-left">
            <h3 className="text-lg font-semibold text-foreground">MACD Filter</h3>
            <p className="text-sm text-muted-foreground">
              {formState.enabled ? 'Active' : 'Disabled'} - {formState.timeframe} timeframe
            </p>
          </div>
        </div>
        <svg
          className={`h-5 w-5 text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="px-6 pb-6 border-t border-border/50">
          <div className="pt-4 space-y-4">
            {/* Enable/Disable Toggle */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formState.enabled}
                  onChange={(e) => handleChange('enabled', e.target.checked)}
                  className="w-5 h-5 rounded border-border text-primary focus:ring-primary/50"
                />
                <span className="text-foreground font-medium">Enable MACD Filter</span>
              </label>
              <span className="text-xs text-muted-foreground">
                Controls whether MACD filter affects trading
              </span>
            </div>

            {/* MACD Periods */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Fast Period */}
              <div className="space-y-1">
                <label htmlFor="fastPeriod" className="block text-sm font-medium text-foreground">
                  Fast Period
                </label>
                <input
                  id="fastPeriod"
                  type="number"
                  min={PERIOD_MIN}
                  max={PERIOD_MAX}
                  value={formState.fastPeriod}
                  onChange={(e) => handleChange('fastPeriod', parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                />
                {errors.fastPeriod && (
                  <p className="text-xs text-destructive">{errors.fastPeriod}</p>
                )}
                <p className="text-xs text-muted-foreground">Default: 12</p>
              </div>

              {/* Slow Period */}
              <div className="space-y-1">
                <label htmlFor="slowPeriod" className="block text-sm font-medium text-foreground">
                  Slow Period
                </label>
                <input
                  id="slowPeriod"
                  type="number"
                  min={PERIOD_MIN}
                  max={PERIOD_MAX}
                  value={formState.slowPeriod}
                  onChange={(e) => handleChange('slowPeriod', parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                />
                {errors.slowPeriod && (
                  <p className="text-xs text-destructive">{errors.slowPeriod}</p>
                )}
                <p className="text-xs text-muted-foreground">Default: 26</p>
              </div>

              {/* Signal Period */}
              <div className="space-y-1">
                <label htmlFor="signalPeriod" className="block text-sm font-medium text-foreground">
                  Signal Period
                </label>
                <input
                  id="signalPeriod"
                  type="number"
                  min={PERIOD_MIN}
                  max={PERIOD_MAX}
                  value={formState.signalPeriod}
                  onChange={(e) => handleChange('signalPeriod', parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                />
                {errors.signalPeriod && (
                  <p className="text-xs text-destructive">{errors.signalPeriod}</p>
                )}
                <p className="text-xs text-muted-foreground">Default: 9</p>
              </div>
            </div>

            {/* Timeframe Selector */}
            <div className="space-y-1">
              <label htmlFor="timeframe" className="block text-sm font-medium text-foreground">
                Timeframe
              </label>
              <select
                id="timeframe"
                value={formState.timeframe}
                onChange={(e) => handleChange('timeframe', e.target.value)}
                className="w-full md:w-1/3 px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf.value} value={tf.value}>
                    {tf.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                Candle timeframe for MACD calculation
              </p>
            </div>

            {/* Action Buttons */}
            {hasChanges && (
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={updateMutation.isPending || Object.keys(errors).length > 0}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {updateMutation.isPending && (
                    <svg
                      className="animate-spin h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  )}
                  Save MACD Settings
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  Reset
                </button>
                {updateMutation.isSuccess && (
                  <span className="text-sm text-green-500 flex items-center gap-1">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Saved!
                  </span>
                )}
                {updateMutation.isError && (
                  <span className="text-sm text-destructive">
                    Failed to save
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
