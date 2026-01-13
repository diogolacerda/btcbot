import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { AdvancedSettings, CurrentMarket } from '@/../product/sections/strategy/types'

interface AdvancedSettingsSectionProps {
  advancedSettings: AdvancedSettings
  currentMarket: CurrentMarket
  onUpdate?: (settings: AdvancedSettings) => void
}

export function AdvancedSettingsSection({
  advancedSettings,
  currentMarket,
  onUpdate,
}: AdvancedSettingsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [settings, setSettings] = useState(advancedSettings)

  const handleDynamicTPToggle = () => {
    const newSettings = {
      ...settings,
      dynamicTP: {
        ...settings.dynamicTP,
        enabled: !settings.dynamicTP.enabled,
      },
    }
    setSettings(newSettings)
    onUpdate?.(newSettings)
  }

  const handleDynamicTPChange = (field: string, value: number) => {
    const newSettings = {
      ...settings,
      dynamicTP: {
        ...settings.dynamicTP,
        [field]: value,
      },
    }
    setSettings(newSettings)
    onUpdate?.(newSettings)
  }

  const handleAutoReactivationChange = (mode: 'immediate' | 'full-cycle') => {
    const newSettings = {
      ...settings,
      autoReactivationMode: mode,
    }
    setSettings(newSettings)
    onUpdate?.(newSettings)
  }

  // Calculate preview TP based on current funding rate
  const calculatePreviewTP = () => {
    if (!settings.dynamicTP.enabled) return settings.dynamicTP.baseTP

    const fundingRate = currentMarket.fundingRate
    let adjustedTP = settings.dynamicTP.baseTP

    // If longs pay (positive funding rate), increase TP
    if (fundingRate > 0) {
      adjustedTP = Math.min(
        settings.dynamicTP.baseTP + fundingRate * 100 + settings.dynamicTP.safetyMargin,
        settings.dynamicTP.maxTP
      )
    } else {
      // If shorts pay (negative funding rate), decrease TP
      adjustedTP = Math.max(
        settings.dynamicTP.baseTP + fundingRate * 100 - settings.dynamicTP.safetyMargin,
        settings.dynamicTP.minTP
      )
    }

    return adjustedTP
  }

  const previewTP = calculatePreviewTP()

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
      {/* Header - Always Visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Advanced Settings
          </h3>
          <span className="text-xs text-amber-600 dark:text-amber-400 font-medium uppercase tracking-wide">
            Optional
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-slate-500 dark:text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-500 dark:text-slate-400" />
        )}
      </button>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="px-6 pb-6 space-y-6 border-t border-slate-200 dark:border-slate-700 pt-6">
          {/* Dynamic TP */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Dynamic Take Profit
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Adjust TP based on funding rate
                </p>
              </div>

              <label className="flex items-center gap-3 cursor-pointer">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  {settings.dynamicTP.enabled ? 'Enabled' : 'Disabled'}
                </span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={settings.dynamicTP.enabled}
                    onChange={handleDynamicTPToggle}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-emerald-500 dark:peer-focus:ring-emerald-400 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </div>
              </label>
            </div>

            {settings.dynamicTP.enabled && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Base TP (%)
                    </label>
                    <input
                      type="number"
                      value={settings.dynamicTP.baseTP}
                      onChange={(e) =>
                        handleDynamicTPChange('baseTP', parseFloat(e.target.value))
                      }
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Min TP (%)
                    </label>
                    <input
                      type="number"
                      value={settings.dynamicTP.minTP}
                      onChange={(e) => handleDynamicTPChange('minTP', parseFloat(e.target.value))}
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Max TP (%)
                    </label>
                    <input
                      type="number"
                      value={settings.dynamicTP.maxTP}
                      onChange={(e) => handleDynamicTPChange('maxTP', parseFloat(e.target.value))}
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Safety Margin (%)
                    </label>
                    <input
                      type="number"
                      value={settings.dynamicTP.safetyMargin}
                      onChange={(e) =>
                        handleDynamicTPChange('safetyMargin', parseFloat(e.target.value))
                      }
                      min="0"
                      max="1"
                      step="0.01"
                      className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Check Interval (minutes)
                  </label>
                  <input
                    type="number"
                    value={settings.dynamicTP.checkInterval}
                    onChange={(e) =>
                      handleDynamicTPChange('checkInterval', parseInt(e.target.value))
                    }
                    min="1"
                    max="1440"
                    className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                  />
                </div>

                {/* Preview */}
                <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    <span className="font-medium">Preview:</span> With current funding rate (
                    {(currentMarket.fundingRate * 100).toFixed(4)}%), TP would be{' '}
                    <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                      {previewTP.toFixed(2)}%
                    </span>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Auto-Reactivation Mode */}
          <div>
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
              Auto-Reactivation Mode
            </h4>

            <div className="space-y-3">
              <label
                className={`flex items-start gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 ${
                  settings.autoReactivationMode === 'immediate'
                    ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30'
                    : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="autoReactivation"
                  value="immediate"
                  checked={settings.autoReactivationMode === 'immediate'}
                  onChange={(e) => handleAutoReactivationChange(e.target.value as 'immediate')}
                  className="mt-0.5 w-4 h-4 text-emerald-600 focus:ring-emerald-500"
                />
                <div className="flex-1">
                  <span className="font-medium text-slate-900 dark:text-slate-100">Immediate</span>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    Restart cycle when MACD turns bullish again (keeps existing positions)
                  </p>
                </div>
              </label>

              <label
                className={`flex items-start gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 ${
                  settings.autoReactivationMode === 'full-cycle'
                    ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30'
                    : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="autoReactivation"
                  value="full-cycle"
                  checked={settings.autoReactivationMode === 'full-cycle'}
                  onChange={(e) => handleAutoReactivationChange(e.target.value as 'full-cycle')}
                  className="mt-0.5 w-4 h-4 text-emerald-600 focus:ring-emerald-500"
                />
                <div className="flex-1">
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    Full Cycle
                  </span>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    Wait for all positions to close before restarting (slower but safer)
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
