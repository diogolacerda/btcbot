/**
 * Risk Summary Card (FE-STRAT-002)
 *
 * Displays calculated risk metrics based on current form values.
 * Updates in real-time as the user modifies strategy parameters.
 */

import type { StrategyFormValues } from './strategySchema'

// ============================================================================
// Types
// ============================================================================

interface RiskSummaryCardProps {
  values: StrategyFormValues
}

interface MetricRowProps {
  label: string
  value: string
  variant?: 'default' | 'highlight' | 'warning' | 'success'
  tooltip?: string
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatCurrency(value: number): string {
  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`
}

// ============================================================================
// Sub-components
// ============================================================================

function MetricRow({
  label,
  value,
  variant = 'default',
  tooltip,
}: MetricRowProps) {
  const valueClasses = {
    default: 'text-foreground',
    highlight: 'text-primary font-semibold',
    warning: 'text-yellow-500',
    success: 'text-green-500',
  }

  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-sm text-muted-foreground" title={tooltip}>
        {label}
      </span>
      <span className={`text-sm font-medium ${valueClasses[variant]}`}>
        {value}
      </span>
    </div>
  )
}

function SectionDivider() {
  return <div className="border-t border-border/50 my-2" />
}

// ============================================================================
// Risk Calculation Functions
// ============================================================================

function calculateRiskMetrics(values: StrategyFormValues) {
  const { leverage, orderSizeUsdt, maxTotalOrders, takeProfitPercent } = values

  // Notional value per order (order size * leverage)
  const notionalPerOrder = orderSizeUsdt * leverage

  // Maximum capital at risk (all orders filled)
  const maxCapitalAtRisk = orderSizeUsdt * maxTotalOrders

  // Maximum notional exposure
  const maxNotionalExposure = notionalPerOrder * maxTotalOrders

  // Expected profit per order (at TP)
  const expectedProfitPerOrder = (notionalPerOrder * takeProfitPercent) / 100

  // Maximum profit if all orders hit TP
  const maxPotentialProfit = expectedProfitPerOrder * maxTotalOrders

  // Liquidation distance (rough estimate: 100% / leverage)
  const liquidationDistance = 100 / leverage

  // Risk rating based on leverage
  let riskLevel: 'Low' | 'Medium' | 'High' | 'Very High'
  if (leverage <= 5) riskLevel = 'Low'
  else if (leverage <= 20) riskLevel = 'Medium'
  else if (leverage <= 50) riskLevel = 'High'
  else riskLevel = 'Very High'

  return {
    notionalPerOrder,
    maxCapitalAtRisk,
    maxNotionalExposure,
    expectedProfitPerOrder,
    maxPotentialProfit,
    liquidationDistance,
    riskLevel,
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function RiskSummaryCard({ values }: RiskSummaryCardProps) {
  const metrics = calculateRiskMetrics(values)

  const riskLevelColors = {
    Low: 'text-green-500 bg-green-500/10',
    Medium: 'text-yellow-500 bg-yellow-500/10',
    High: 'text-orange-500 bg-orange-500/10',
    'Very High': 'text-red-500 bg-red-500/10',
  }

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Risk Summary</h3>
        <span
          className={`px-2 py-0.5 text-xs font-medium rounded-full ${riskLevelColors[metrics.riskLevel]}`}
        >
          {metrics.riskLevel} Risk
        </span>
      </div>

      <div className="space-y-1">
        {/* Position Info */}
        <MetricRow
          label="Leverage"
          value={`${values.leverage}x`}
          variant="highlight"
        />
        <MetricRow
          label="Order Size"
          value={formatCurrency(values.orderSizeUsdt)}
        />
        <MetricRow
          label="Notional / Order"
          value={formatCurrency(metrics.notionalPerOrder)}
          tooltip="Order size multiplied by leverage"
        />

        <SectionDivider />

        {/* Grid Info */}
        <MetricRow label="Max Orders" value={`${values.maxTotalOrders}`} />
        <MetricRow
          label="Grid Range"
          value={formatPercent(values.rangePercent)}
        />
        <MetricRow
          label="Max Capital at Risk"
          value={formatCurrency(metrics.maxCapitalAtRisk)}
          variant="warning"
          tooltip="Total margin if all orders are filled"
        />

        <SectionDivider />

        {/* Profit Projections */}
        <MetricRow
          label="Take Profit"
          value={formatPercent(values.takeProfitPercent)}
        />
        <MetricRow
          label="Est. Profit / Order"
          value={formatCurrency(metrics.expectedProfitPerOrder)}
          variant="success"
          tooltip="Expected profit when TP hits"
        />
        <MetricRow
          label="Max Potential Profit"
          value={formatCurrency(metrics.maxPotentialProfit)}
          variant="success"
          tooltip="If all orders hit TP"
        />

        <SectionDivider />

        {/* Risk Metrics */}
        <MetricRow
          label="Max Notional Exposure"
          value={formatCurrency(metrics.maxNotionalExposure)}
          tooltip="Total notional if all orders filled"
        />
        <MetricRow
          label="Liquidation Distance"
          value={`~${formatPercent(metrics.liquidationDistance)}`}
          variant={metrics.liquidationDistance < 2 ? 'warning' : 'default'}
          tooltip="Approximate price move to liquidation"
        />
      </div>

      {/* Warning for high leverage */}
      {values.leverage >= 50 && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-md">
          <div className="flex items-start gap-2">
            <svg
              className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
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
            <div>
              <p className="text-sm font-medium text-red-500">
                High Leverage Warning
              </p>
              <p className="text-xs text-red-400 mt-1">
                Leverage above 50x significantly increases liquidation risk.
                Small price movements can result in total loss of margin.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Dynamic TP indicator */}
      {values.tpDynamicEnabled && (
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-md">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-blue-500">
                Dynamic TP Enabled
              </p>
              <p className="text-xs text-blue-400 mt-1">
                TP will adjust between {formatPercent(values.tpDynamicMin)} -{' '}
                {formatPercent(values.tpDynamicMax)} based on funding rate
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
