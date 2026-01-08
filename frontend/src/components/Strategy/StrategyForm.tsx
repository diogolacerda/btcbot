/**
 * Strategy Create/Edit Form (FE-STRAT-002)
 *
 * Comprehensive form for configuring trading strategy parameters.
 * Uses React Hook Form with Zod validation.
 *
 * Sections:
 * - Basic Info: Name, Symbol
 * - Risk Parameters: Leverage, Position Size, Margin Mode
 * - Take Profit: TP%, Dynamic TP settings
 * - Grid Settings: Spacing, Range, Max Orders, Anchor Mode
 */

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import {
  strategyFormSchema,
  defaultStrategyValues,
  LEVERAGE_MIN,
  LEVERAGE_MAX,
  MARGIN_MODES,
  SPACING_TYPES,
  ANCHOR_MODES,
  type StrategyFormValues,
} from './strategySchema'
import { RiskSummaryCard } from './RiskSummaryCard'

// ============================================================================
// Types
// ============================================================================

interface StrategyFormProps {
  mode: 'create' | 'edit'
  initialValues?: Partial<StrategyFormValues>
  onSubmit: (data: StrategyFormValues) => Promise<void>
  isSubmitting?: boolean
  /** Optional content to render before the form action buttons */
  children?: React.ReactNode
}

// ============================================================================
// Helper Components
// ============================================================================

interface FormSectionProps {
  title: string
  description?: string
  children: React.ReactNode
}

function FormSection({ title, description, children }: FormSectionProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      <div className="space-y-4">{children}</div>
    </div>
  )
}

interface FormFieldProps {
  label: string
  htmlFor: string
  error?: string
  hint?: string
  children: React.ReactNode
  required?: boolean
}

function FormField({
  label,
  htmlFor,
  error,
  hint,
  children,
  required,
}: FormFieldProps) {
  return (
    <div className="space-y-1">
      <label
        htmlFor={htmlFor}
        className="block text-sm font-medium text-foreground"
      >
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </label>
      {children}
      {hint && !error && (
        <p className="text-xs text-muted-foreground">{hint}</p>
      )}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function StrategyForm({
  mode,
  initialValues,
  onSubmit,
  isSubmitting = false,
  children,
}: StrategyFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<StrategyFormValues>({
    resolver: zodResolver(strategyFormSchema),
    defaultValues: { ...defaultStrategyValues, ...initialValues },
  })

  // Watch values for dynamic UI and risk calculations
  const watchedValues = watch()
  const tpDynamicEnabled = watch('tpDynamicEnabled')

  const handleFormSubmit = handleSubmit(async (data) => {
    await onSubmit(data)
  })

  return (
    <form onSubmit={handleFormSubmit} className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Form Sections */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Info Section */}
          <FormSection
            title="Basic Info"
            description="Name and trading pair for this strategy"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                label="Strategy Name"
                htmlFor="name"
                error={errors.name?.message}
                required
              >
                <input
                  id="name"
                  type="text"
                  placeholder="e.g., Conservative Grid"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                  {...register('name')}
                />
              </FormField>

              <FormField
                label="Symbol"
                htmlFor="symbol"
                error={errors.symbol?.message}
                hint="Trading pair (e.g., BTC-USDT)"
                required
              >
                <input
                  id="symbol"
                  type="text"
                  placeholder="BTC-USDT"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                  {...register('symbol')}
                />
              </FormField>
            </div>
          </FormSection>

          {/* Risk Parameters Section */}
          <FormSection
            title="Risk Parameters"
            description="Configure leverage, position size, and margin mode"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FormField
                label={`Leverage (${LEVERAGE_MIN}-${LEVERAGE_MAX}x)`}
                htmlFor="leverage"
                error={errors.leverage?.message}
                required
              >
                <div className="space-y-2">
                  <input
                    id="leverage"
                    type="range"
                    min={LEVERAGE_MIN}
                    max={LEVERAGE_MAX}
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                    {...register('leverage', { valueAsNumber: true })}
                  />
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{LEVERAGE_MIN}x</span>
                    <span className="font-medium text-primary">
                      {watchedValues.leverage}x
                    </span>
                    <span className="text-muted-foreground">{LEVERAGE_MAX}x</span>
                  </div>
                </div>
              </FormField>

              <FormField
                label="Order Size (USDT)"
                htmlFor="orderSizeUsdt"
                error={errors.orderSizeUsdt?.message}
                required
              >
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    $
                  </span>
                  <input
                    id="orderSizeUsdt"
                    type="number"
                    step="0.01"
                    min="1"
                    placeholder="100.00"
                    className="w-full pl-7 pr-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                    {...register('orderSizeUsdt', { valueAsNumber: true })}
                  />
                </div>
              </FormField>

              <FormField
                label="Margin Mode"
                htmlFor="marginMode"
                error={errors.marginMode?.message}
                required
              >
                <select
                  id="marginMode"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary capitalize"
                  {...register('marginMode')}
                >
                  {MARGIN_MODES.map((mode) => (
                    <option key={mode} value={mode} className="capitalize">
                      {mode}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>
          </FormSection>

          {/* Take Profit Section */}
          <FormSection
            title="Take Profit"
            description="Configure take profit percentage and dynamic adjustments"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  label="Take Profit %"
                  htmlFor="takeProfitPercent"
                  error={errors.takeProfitPercent?.message}
                  hint="Base TP percentage for each trade"
                  required
                >
                  <div className="relative">
                    <input
                      id="takeProfitPercent"
                      type="number"
                      step="0.01"
                      min="0.01"
                      max="10"
                      placeholder="0.50"
                      className="w-full px-3 py-2 pr-8 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                      {...register('takeProfitPercent', { valueAsNumber: true })}
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                      %
                    </span>
                  </div>
                </FormField>

                <FormField
                  label="Dynamic TP"
                  htmlFor="tpDynamicEnabled"
                  hint="Adjust TP based on funding rate"
                >
                  <label className="flex items-center gap-3 cursor-pointer py-2">
                    <input
                      id="tpDynamicEnabled"
                      type="checkbox"
                      className="w-5 h-5 rounded border-border text-primary focus:ring-primary/50"
                      {...register('tpDynamicEnabled')}
                    />
                    <span className="text-foreground">
                      Enable Dynamic TP Adjustments
                    </span>
                  </label>
                </FormField>
              </div>

              {/* Dynamic TP Sub-fields (shown when enabled) */}
              {tpDynamicEnabled && (
                <div className="mt-4 p-4 bg-muted/30 rounded-lg border border-border/50">
                  <h4 className="text-sm font-medium text-foreground mb-3">
                    Dynamic TP Settings
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <FormField
                      label="Base TP %"
                      htmlFor="tpDynamicBase"
                      error={errors.tpDynamicBase?.message}
                    >
                      <input
                        id="tpDynamicBase"
                        type="number"
                        step="0.01"
                        min="0.01"
                        placeholder="0.30"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                        {...register('tpDynamicBase', { valueAsNumber: true })}
                      />
                    </FormField>

                    <FormField
                      label="Min TP %"
                      htmlFor="tpDynamicMin"
                      error={errors.tpDynamicMin?.message}
                    >
                      <input
                        id="tpDynamicMin"
                        type="number"
                        step="0.01"
                        min="0.01"
                        placeholder="0.30"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                        {...register('tpDynamicMin', { valueAsNumber: true })}
                      />
                    </FormField>

                    <FormField
                      label="Max TP %"
                      htmlFor="tpDynamicMax"
                      error={errors.tpDynamicMax?.message}
                    >
                      <input
                        id="tpDynamicMax"
                        type="number"
                        step="0.01"
                        min="0.01"
                        placeholder="1.00"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                        {...register('tpDynamicMax', { valueAsNumber: true })}
                      />
                    </FormField>

                    <FormField
                      label="Safety Margin %"
                      htmlFor="tpDynamicSafetyMargin"
                      error={errors.tpDynamicSafetyMargin?.message}
                      hint="Added above funding cost"
                    >
                      <input
                        id="tpDynamicSafetyMargin"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="0.05"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                        {...register('tpDynamicSafetyMargin', {
                          valueAsNumber: true,
                        })}
                      />
                    </FormField>

                    <FormField
                      label="Check Interval (min)"
                      htmlFor="tpDynamicCheckInterval"
                      error={errors.tpDynamicCheckInterval?.message}
                      hint="How often to check funding"
                    >
                      <input
                        id="tpDynamicCheckInterval"
                        type="number"
                        step="1"
                        min="1"
                        placeholder="60"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                        {...register('tpDynamicCheckInterval', {
                          valueAsNumber: true,
                        })}
                      />
                    </FormField>
                  </div>
                </div>
              )}
            </div>
          </FormSection>

          {/* Grid Settings Section */}
          <FormSection
            title="Grid Settings"
            description="Configure grid levels, spacing, and anchoring"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                label="Spacing Type"
                htmlFor="spacingType"
                error={errors.spacingType?.message}
                required
              >
                <select
                  id="spacingType"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary capitalize"
                  {...register('spacingType')}
                >
                  {SPACING_TYPES.map((type) => (
                    <option key={type} value={type} className="capitalize">
                      {type}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField
                label={
                  watchedValues.spacingType === 'fixed'
                    ? 'Spacing Value (USDT)'
                    : 'Spacing Value (%)'
                }
                htmlFor="spacingValue"
                error={errors.spacingValue?.message}
                required
              >
                <div className="relative">
                  {watchedValues.spacingType === 'fixed' && (
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                      $
                    </span>
                  )}
                  <input
                    id="spacingValue"
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder={
                      watchedValues.spacingType === 'fixed' ? '100' : '0.5'
                    }
                    className={`w-full py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary ${
                      watchedValues.spacingType === 'fixed'
                        ? 'pl-7 pr-3'
                        : 'px-3 pr-8'
                    }`}
                    {...register('spacingValue', { valueAsNumber: true })}
                  />
                  {watchedValues.spacingType === 'percentage' && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                      %
                    </span>
                  )}
                </div>
              </FormField>

              <FormField
                label="Grid Range %"
                htmlFor="rangePercent"
                error={errors.rangePercent?.message}
                hint="Distance from current price to grid boundaries"
                required
              >
                <div className="relative">
                  <input
                    id="rangePercent"
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="50"
                    placeholder="5.0"
                    className="w-full px-3 py-2 pr-8 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                    {...register('rangePercent', { valueAsNumber: true })}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    %
                  </span>
                </div>
              </FormField>

              <FormField
                label="Max Orders"
                htmlFor="maxTotalOrders"
                error={errors.maxTotalOrders?.message}
                hint="Maximum concurrent grid orders"
                required
              >
                <input
                  id="maxTotalOrders"
                  type="number"
                  step="1"
                  min="1"
                  max="50"
                  placeholder="10"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                  {...register('maxTotalOrders', { valueAsNumber: true })}
                />
              </FormField>

              <FormField
                label="Anchor Mode"
                htmlFor="anchorMode"
                error={errors.anchorMode?.message}
                hint="Align grid levels to round numbers"
              >
                <select
                  id="anchorMode"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                  {...register('anchorMode')}
                >
                  {ANCHOR_MODES.map((anchorMode) => (
                    <option key={anchorMode} value={anchorMode}>
                      {anchorMode === 'none'
                        ? 'None'
                        : anchorMode === 'hundred'
                          ? '$100 multiples'
                          : '$1000 multiples'}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField
                label="Anchor Threshold"
                htmlFor="anchorThreshold"
                error={errors.anchorThreshold?.message}
                hint="Threshold for anchor alignment"
              >
                <input
                  id="anchorThreshold"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="100"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                  {...register('anchorThreshold', { valueAsNumber: true })}
                />
              </FormField>
            </div>
          </FormSection>
        </div>

        {/* Right Column - Risk Summary */}
        <div className="lg:col-span-1">
          <div className="sticky top-6">
            <RiskSummaryCard values={watchedValues} />
          </div>
        </div>
      </div>

      {/* Additional content slot (e.g., MACD Filter Section) */}
      {children}

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-4 pt-4 border-t border-border">
        <Link
          to="/strategies"
          className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          Cancel
        </Link>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isSubmitting && (
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
          {mode === 'create' ? 'Create Strategy' : 'Save Changes'}
        </button>
      </div>
    </form>
  )
}
