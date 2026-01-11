/**
 * EMA Filter Configuration Section
 *
 * Collapsible section for configuring EMA filter parameters.
 * Only shown in edit mode since the config is created with the strategy.
 */

import { useState, useMemo } from 'react'
import {
  useEMAFilterConfig,
  useUpdateEMAFilterConfig,
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
const PERIOD_MAX = 200

// ============================================================================
// Types
// ============================================================================

interface EMAFilterSectionProps {
  strategyId: string
}

interface FormState {
  enabled: boolean
  period: number
  timeframe: MACDTimeframe
  allowOnRising: boolean
  allowOnFalling: boolean
}

// ============================================================================
// Component
// ============================================================================

export function EMAFilterSection({ strategyId }: EMAFilterSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [localChanges, setLocalChanges] = useState<Partial<FormState> | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: emaConfig, isLoading, isError, error } = useEMAFilterConfig(strategyId)
  const updateMutation = useUpdateEMAFilterConfig()

  // Check if error is a 404 (config doesn't exist yet)
  const isNotFound = isError && error instanceof Error &&
    (error.message.includes('404') || error.message.includes('not found'))

  // Derive form state from server data + local changes
  const formState: FormState = useMemo(() => {
    const serverState: FormState = emaConfig
      ? {
          enabled: emaConfig.enabled,
          period: emaConfig.period,
          timeframe: emaConfig.timeframe,
          allowOnRising: emaConfig.allowOnRising,
          allowOnFalling: emaConfig.allowOnFalling,
        }
      : {
          enabled: false,
          period: 13,
          timeframe: '1h',
          allowOnRising: true,
          allowOnFalling: false,
        }

    return localChanges ? { ...serverState, ...localChanges } : serverState
  }, [emaConfig, localChanges])

  const hasChanges = localChanges !== null

  // Validation
  const validate = (state: FormState): Record<string, string> => {
    const newErrors: Record<string, string> = {}

    if (state.period < PERIOD_MIN || state.period > PERIOD_MAX) {
      newErrors.period = `Must be between ${PERIOD_MIN} and ${PERIOD_MAX}`
    }

    if (state.enabled && !state.allowOnRising && !state.allowOnFalling) {
      newErrors.behavior = 'At least one trading direction must be allowed'
    }

    return newErrors
  }

  const handleChange = (field: keyof FormState, value: boolean | number | string) => {
    const newChanges = { ...localChanges, [field]: value }
    setLocalChanges(newChanges)

    // Compute new state for validation
    const serverState: FormState = emaConfig
      ? {
          enabled: emaConfig.enabled,
          period: emaConfig.period,
          timeframe: emaConfig.timeframe,
          allowOnRising: emaConfig.allowOnRising,
          allowOnFalling: emaConfig.allowOnFalling,
        }
      : {
          enabled: false,
          period: 13,
          timeframe: '1h',
          allowOnRising: true,
          allowOnFalling: false,
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

  // Only show error for non-404 errors (404 means config doesn't exist yet, which is OK)
  if (isError && !isNotFound) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6">
        <div className="flex items-center gap-2 text-destructive">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Failed to load EMA filter configuration</span>
        </div>
      </div>
    )
  }

  // For 404 (not found), we show the form with defaults so user can create the config
  const configExists = emaConfig !== undefined && !isNotFound

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
            <h3 className="text-lg font-semibold text-foreground">EMA Filter</h3>
            <p className="text-sm text-muted-foreground">
              {configExists
                ? `${formState.enabled ? 'Active' : 'Disabled'} - ${formState.period} period, ${formState.timeframe} timeframe`
                : 'Not configured - click to set up'}
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
                <span className="text-foreground font-medium">Enable EMA Filter</span>
              </label>
              <span className="text-xs text-muted-foreground">
                Controls whether EMA filter affects trading
              </span>
            </div>

            {/* Period and Timeframe */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Period */}
              <div className="space-y-1">
                <label htmlFor="emaPeriod" className="block text-sm font-medium text-foreground">
                  Period
                </label>
                <input
                  id="emaPeriod"
                  type="number"
                  min={PERIOD_MIN}
                  max={PERIOD_MAX}
                  value={formState.period}
                  onChange={(e) => handleChange('period', parseInt(e.target.value) || 0)}
                  disabled={!formState.enabled}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed"
                />
                {errors.period && (
                  <p className="text-xs text-destructive">{errors.period}</p>
                )}
                <p className="text-xs text-muted-foreground">EMA period ({PERIOD_MIN}-{PERIOD_MAX})</p>
              </div>

              {/* Timeframe Selector */}
              <div className="space-y-1">
                <label htmlFor="emaTimeframe" className="block text-sm font-medium text-foreground">
                  Timeframe
                </label>
                <select
                  id="emaTimeframe"
                  value={formState.timeframe}
                  onChange={(e) => handleChange('timeframe', e.target.value)}
                  disabled={!formState.enabled}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {TIMEFRAMES.map((tf) => (
                    <option key={tf.value} value={tf.value}>
                      {tf.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground">
                  Candle timeframe for EMA calculation
                </p>
              </div>
            </div>

            {/* Trading Behavior */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">
                Trading Behavior
              </label>
              <div className="space-y-2 p-3 bg-muted/30 rounded-md">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formState.allowOnRising}
                    onChange={(e) => handleChange('allowOnRising', e.target.checked)}
                    disabled={!formState.enabled}
                    className="w-4 h-4 rounded border-border text-primary focus:ring-primary/50 disabled:opacity-50"
                  />
                  <span className={`text-sm ${!formState.enabled ? 'text-muted-foreground' : 'text-foreground'}`}>
                    Allow trades when EMA is rising
                  </span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formState.allowOnFalling}
                    onChange={(e) => handleChange('allowOnFalling', e.target.checked)}
                    disabled={!formState.enabled}
                    className="w-4 h-4 rounded border-border text-primary focus:ring-primary/50 disabled:opacity-50"
                  />
                  <span className={`text-sm ${!formState.enabled ? 'text-muted-foreground' : 'text-foreground'}`}>
                    Allow trades when EMA is falling
                  </span>
                </label>
              </div>
              {errors.behavior && (
                <p className="text-xs text-destructive">{errors.behavior}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Configure when the bot can create new orders based on EMA direction
              </p>
            </div>

            {/* Action Buttons - show always if config doesn't exist, or when there are changes */}
            {(hasChanges || !configExists) && (
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
                  {configExists ? 'Save EMA Settings' : 'Create EMA Settings'}
                </button>
                {hasChanges && (
                  <button
                    type="button"
                    onClick={handleReset}
                    disabled={updateMutation.isPending}
                    className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Reset
                  </button>
                )}
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
