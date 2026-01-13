import { useState } from 'react'
import type { GridSettings, CurrentMarket } from '@/../product/sections/strategy/types'

interface GridSettingsSectionProps {
  gridSettings: GridSettings
  currentMarket: CurrentMarket
  onUpdate?: (settings: GridSettings) => void
}

export function GridSettingsSection({
  gridSettings,
  currentMarket,
  onUpdate,
}: GridSettingsSectionProps) {
  const [settings, setSettings] = useState(gridSettings)

  const handleChange = (field: keyof GridSettings, value: string | number) => {
    const newSettings = { ...settings, [field]: value }
    setSettings(newSettings)
    onUpdate?.(newSettings)
  }

  const calculateGridRange = () => {
    const range = (currentMarket.btcPrice * settings.gridRange) / 100
    const minPrice = currentMarket.btcPrice - range
    const maxPrice = currentMarket.btcPrice + range
    return { minPrice, maxPrice }
  }

  const calculateTakeProfit = () => {
    const tpAmount = currentMarket.btcPrice * (settings.takeProfit / 100)
    const tpPrice = currentMarket.btcPrice + tpAmount
    return tpPrice
  }

  const { minPrice, maxPrice } = calculateGridRange()
  const tpPrice = calculateTakeProfit()

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Grid Settings
      </h3>

      <div className="space-y-6">
        {/* Spacing Type */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            Spacing Type
          </label>
          <div className="flex gap-4">
            <label
              className={`flex-1 flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 ${
                settings.spacingType === 'fixed'
                  ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30'
                  : 'border-slate-200 dark:border-slate-700'
              }`}
            >
              <input
                type="radio"
                name="spacingType"
                value="fixed"
                checked={settings.spacingType === 'fixed'}
                onChange={(e) => handleChange('spacingType', e.target.value)}
                className="w-4 h-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div className="flex-1">
                <span className="font-medium text-slate-900 dark:text-slate-100">Fixed ($)</span>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Orders spaced by fixed dollar amount
                </p>
              </div>
            </label>

            <label
              className={`flex-1 flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 ${
                settings.spacingType === 'percentage'
                  ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30'
                  : 'border-slate-200 dark:border-slate-700'
              }`}
            >
              <input
                type="radio"
                name="spacingType"
                value="percentage"
                checked={settings.spacingType === 'percentage'}
                onChange={(e) => handleChange('spacingType', e.target.value)}
                className="w-4 h-4 text-emerald-600 focus:ring-emerald-500"
              />
              <div className="flex-1">
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  Percentage (%)
                </span>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Orders spaced by % of price
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Spacing Value */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Spacing Value {settings.spacingType === 'fixed' ? '($)' : '(%)'}
          </label>
          <input
            type="number"
            value={settings.spacingValue}
            onChange={(e) => handleChange('spacingValue', parseFloat(e.target.value))}
            min={settings.spacingType === 'fixed' ? '10' : '0.01'}
            step={settings.spacingType === 'fixed' ? '10' : '0.01'}
            className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
          />
          {settings.spacingType === 'fixed' && settings.spacingValue < 10 && (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              ⚠️ Spacing too tight may result in high trading fees
            </p>
          )}
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {settings.spacingType === 'fixed'
              ? `Orders at $${currentMarket.btcPrice.toFixed(0)}, $${(currentMarket.btcPrice - settings.spacingValue).toFixed(0)}, $${(currentMarket.btcPrice - settings.spacingValue * 2).toFixed(0)}...`
              : `Orders at $${currentMarket.btcPrice.toFixed(0)}, $${(currentMarket.btcPrice * (1 - settings.spacingValue / 100)).toFixed(0)}, $${(currentMarket.btcPrice * (1 - (settings.spacingValue * 2) / 100)).toFixed(0)}...`}
          </p>
        </div>

        {/* Grid Range */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Range from Current Price (±%)
          </label>
          <input
            type="number"
            value={settings.gridRange}
            onChange={(e) => handleChange('gridRange', parseFloat(e.target.value))}
            min="0.1"
            max="50"
            step="0.1"
            className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            If BTC = ${currentMarket.btcPrice.toFixed(0)}, range is ${minPrice.toFixed(0)} - ${maxPrice.toFixed(0)}
          </p>
        </div>

        {/* Take Profit */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Take Profit Target (%)
          </label>
          <input
            type="number"
            value={settings.takeProfit}
            onChange={(e) => handleChange('takeProfit', parseFloat(e.target.value))}
            min="0.1"
            max="10"
            step="0.1"
            className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
          />
          {settings.takeProfit < 0.1 && (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              ⚠️ Take profit below 0.1% is less than typical trading fees
            </p>
          )}
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Entry ${currentMarket.btcPrice.toFixed(0)} → TP at ${tpPrice.toFixed(0)}
          </p>
        </div>

        {/* Grid Anchor (Advanced) */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Grid Anchor
            <span className="ml-2 text-xs text-amber-600 dark:text-amber-400">Advanced</span>
          </label>
          <select
            value={settings.gridAnchor}
            onChange={(e) => handleChange('gridAnchor', e.target.value)}
            className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
          >
            <option value="none">None</option>
            <option value="align-100s">Align to $100s</option>
          </select>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {settings.gridAnchor === 'none'
              ? 'Grid levels placed naturally based on current price'
              : 'Grid levels aligned to clean price levels ($95,000, $95,100, etc.)'}
          </p>
        </div>
      </div>
    </div>
  )
}
