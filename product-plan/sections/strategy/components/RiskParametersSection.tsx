import { useState } from 'react'
import { HelpCircle } from 'lucide-react'
import type { RiskParameters, RiskSummary } from '@/../product/sections/strategy/types'

interface RiskParametersSectionProps {
  riskParameters: RiskParameters
  riskSummary: RiskSummary
  onUpdate?: (params: RiskParameters) => void
}

export function RiskParametersSection({
  riskParameters,
  riskSummary,
  onUpdate,
}: RiskParametersSectionProps) {
  const [params, setParams] = useState(riskParameters)

  const handleChange = (field: keyof RiskParameters, value: number | string) => {
    const newParams = { ...params, [field]: value }
    setParams(newParams)
    onUpdate?.(newParams)
  }

  const getLeverageRiskLevel = (leverage: number) => {
    if (leverage <= 10) return { level: 'Low', color: 'text-emerald-600 dark:text-emerald-400' }
    if (leverage <= 20) return { level: 'Medium', color: 'text-amber-600 dark:text-amber-400' }
    return { level: 'High', color: 'text-red-600 dark:text-red-400' }
  }

  const leverageRisk = getLeverageRiskLevel(params.leverage)

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Risk Parameters
      </h3>

      <div className="space-y-6">
        {/* Position Size */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Order Size (USDT)
            <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
              Minimum: $5
            </span>
          </label>
          <input
            type="number"
            value={params.positionSize}
            onChange={(e) => handleChange('positionSize', parseFloat(e.target.value))}
            min="5"
            step="10"
            className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            How much USDT each grid order will use
          </p>
        </div>

        {/* Max Total Orders */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Maximum Grid Size
            <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
              Recommended: 5-15
            </span>
          </label>
          <input
            type="number"
            value={params.maxTotalOrders}
            onChange={(e) => handleChange('maxTotalOrders', parseInt(e.target.value))}
            min="1"
            max="50"
            className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Maximum active orders + open positions at once
          </p>
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mt-2">
            Total capital at risk: ${(params.positionSize * params.maxTotalOrders).toFixed(2)}
          </p>
        </div>

        {/* Leverage Slider */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Leverage Multiplier
            </label>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {params.leverage}x
              </span>
              <span className={`text-sm font-medium ${leverageRisk.color}`}>
                {leverageRisk.level} risk
              </span>
            </div>
          </div>

          {/* Slider */}
          <div className="relative">
            <input
              type="range"
              min="1"
              max="125"
              value={params.leverage}
              onChange={(e) => handleChange('leverage', parseInt(e.target.value))}
              className="w-full h-2 bg-gradient-to-r from-emerald-200 via-amber-200 to-red-200 dark:from-emerald-900 dark:via-amber-900 dark:to-red-900 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right,
                  rgb(16 185 129) 0%,
                  rgb(16 185 129) ${(10 / 125) * 100}%,
                  rgb(245 158 11) ${(10 / 125) * 100}%,
                  rgb(245 158 11) ${(20 / 125) * 100}%,
                  rgb(239 68 68) ${(20 / 125) * 100}%,
                  rgb(239 68 68) 100%)`,
              }}
            />
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
              <span>1x</span>
              <span>10x</span>
              <span>20x</span>
              <span>125x</span>
            </div>
          </div>

          {params.leverage > 20 && (
            <div className="mt-2 p-3 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-300">
                ⚠️ High leverage = high risk. Losses can exceed your initial investment.
              </p>
            </div>
          )}

          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            Higher leverage = bigger profits/losses
          </p>
        </div>

        {/* Margin Mode */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            Margin Mode
          </label>
          <div className="flex gap-4">
            <label className="flex-1 flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 ${
              params.marginMode === 'crossed'
                ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30'
                : 'border-slate-200 dark:border-slate-700'
            }">
              <input
                type="radio"
                name="marginMode"
                value="crossed"
                checked={params.marginMode === 'crossed'}
                onChange={(e) => handleChange('marginMode', e.target.value)}
                className="w-4 h-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-900 dark:text-slate-100">Crossed</span>
                  <HelpCircle className="w-4 h-4 text-slate-400" title="All positions share margin (recommended)" />
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Recommended - positions share margin
                </p>
              </div>
            </label>

            <label className={`flex-1 flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 ${
              params.marginMode === 'isolated'
                ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30'
                : 'border-slate-200 dark:border-slate-700'
            }`}>
              <input
                type="radio"
                name="marginMode"
                value="isolated"
                checked={params.marginMode === 'isolated'}
                onChange={(e) => handleChange('marginMode', e.target.value)}
                className="w-4 h-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-900 dark:text-slate-100">Isolated</span>
                  <HelpCircle className="w-4 h-4 text-slate-400" title="Each position has separate margin" />
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Separate margin per position
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Risk Summary */}
        <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
            Risk Summary
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600 dark:text-slate-400">Total Capital:</span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                ${riskSummary.totalCapital.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600 dark:text-slate-400">Capital per Position:</span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                ${riskSummary.capitalPerPosition.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600 dark:text-slate-400">Liquidation Risk:</span>
              <span className={`font-medium capitalize ${getLeverageRiskLevel(params.leverage).color}`}>
                {riskSummary.liquidationRisk}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-600 dark:text-slate-400">Max Loss per Trade:</span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
                ~${riskSummary.maxLossPerTrade.toFixed(2)} ({riskSummary.maxLossPerTradePercent}%)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
