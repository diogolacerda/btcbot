import { useState } from 'react'
import type { MACDFilter } from '@/../product/sections/strategy/types'

interface MACDFilterSectionProps {
  macdFilter: MACDFilter
  onUpdate?: (filter: MACDFilter) => void
}

export function MACDFilterSection({ macdFilter, onUpdate }: MACDFilterSectionProps) {
  const [filter, setFilter] = useState(macdFilter)

  const handleToggle = () => {
    const newFilter = { ...filter, enabled: !filter.enabled }
    setFilter(newFilter)
    onUpdate?.(newFilter)
  }

  const handleChange = (field: keyof MACDFilter, value: boolean | number | string) => {
    const newFilter = { ...filter, [field]: value }
    setFilter(newFilter)
    onUpdate?.(newFilter)
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          MACD Filter
        </h3>

        {/* Enable Toggle */}
        <label className="flex items-center gap-3 cursor-pointer">
          <span className="text-sm text-slate-600 dark:text-slate-400">
            {filter.enabled ? 'Enabled' : 'Disabled'}
          </span>
          <div className="relative">
            <input
              type="checkbox"
              checked={filter.enabled}
              onChange={handleToggle}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-emerald-500 dark:peer-focus:ring-emerald-400 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
          </div>
        </label>
      </div>

      {filter.enabled ? (
        <div className="space-y-4">
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-lg">
            <p className="text-sm text-emerald-700 dark:text-emerald-300">
              ✓ Only trade when MACD indicates bullish trend (recommended)
            </p>
          </div>

          {/* MACD Parameters */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Fast Period
                <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
                  (common: 12)
                </span>
              </label>
              <input
                type="number"
                value={filter.fastPeriod}
                onChange={(e) => handleChange('fastPeriod', parseInt(e.target.value))}
                min="1"
                max="100"
                className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Slow Period
                <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
                  (common: 26)
                </span>
              </label>
              <input
                type="number"
                value={filter.slowPeriod}
                onChange={(e) => handleChange('slowPeriod', parseInt(e.target.value))}
                min="1"
                max="100"
                className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Signal Period
                <span className="ml-2 text-xs text-slate-500 dark:text-slate-400">
                  (common: 9)
                </span>
              </label>
              <input
                type="number"
                value={filter.signalPeriod}
                onChange={(e) => handleChange('signalPeriod', parseInt(e.target.value))}
                min="1"
                max="100"
                className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
              />
            </div>
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Timeframe
            </label>
            <select
              value={filter.timeframe}
              onChange={(e) => handleChange('timeframe', e.target.value)}
              className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
            >
              <option value="15m">15 minutes</option>
              <option value="1h">1 hour</option>
              <option value="4h">4 hours</option>
              <option value="1d">1 day</option>
            </select>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400">
            Standard MACD settings (12, 26, 9) work well for BTC. Strategy will pause when MACD
            turns bearish and resume when bullish.
          </p>
        </div>
      ) : (
        <div className="p-4 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-300">
            ⚠️ Bot will trade continuously without waiting for MACD signals. This increases risk
            during bearish trends.
          </p>
        </div>
      )}
    </div>
  )
}
