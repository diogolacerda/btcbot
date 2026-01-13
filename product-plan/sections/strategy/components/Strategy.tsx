import { useState } from 'react'
import { X, AlertCircle } from 'lucide-react'
import { StrategyStatusCard } from './StrategyStatusCard'
import { RiskParametersSection } from './RiskParametersSection'
import { GridSettingsSection } from './GridSettingsSection'
import { MACDFilterSection } from './MACDFilterSection'
import { AdvancedSettingsSection } from './AdvancedSettingsSection'
import type { StrategyProps } from '@/../product/sections/strategy/types'

type ConfirmAction = 'start' | 'stop' | null

export function Strategy({
  strategy,
  currentMarket,
  riskSummary,
  gridPreview,
  onStart,
  onPause,
  onStop,
  onResume,
  onUpdateRiskParameters,
  onUpdateGridSettings,
  onUpdateMACDFilter,
  onUpdateAdvancedSettings,
  onSave,
}: StrategyProps) {
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null)

  const handleStart = () => {
    setConfirmAction('start')
  }

  const handleStop = () => {
    setConfirmAction('stop')
  }

  const confirmStart = () => {
    onStart?.()
    setConfirmAction(null)
  }

  const confirmStop = () => {
    onStop?.()
    setConfirmAction(null)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Strategy Configuration
        </h1>
      </div>

      {/* Strategy Status & Controls */}
      <StrategyStatusCard
        strategy={strategy}
        onStart={handleStart}
        onPause={onPause}
        onStop={handleStop}
        onResume={onResume}
      />

      {/* Risk Parameters */}
      <RiskParametersSection
        riskParameters={strategy.riskParameters}
        riskSummary={riskSummary}
        onUpdate={onUpdateRiskParameters}
      />

      {/* Grid Settings */}
      <GridSettingsSection
        gridSettings={strategy.gridSettings}
        currentMarket={currentMarket}
        onUpdate={onUpdateGridSettings}
      />

      {/* MACD Filter */}
      <MACDFilterSection macdFilter={strategy.macdFilter} onUpdate={onUpdateMACDFilter} />

      {/* Advanced Settings */}
      <AdvancedSettingsSection
        advancedSettings={strategy.advancedSettings}
        currentMarket={currentMarket}
        onUpdate={onUpdateAdvancedSettings}
      />

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={onSave}
          className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
        >
          Save Changes
        </button>
      </div>

      {/* Start Confirmation Modal */}
      {confirmAction === 'start' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-start gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  Start Strategy?
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Strategy will activate when MACD turns bullish. The bot will start placing grid
                  orders and managing positions automatically.
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setConfirmAction(null)}
                className="flex-1 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={confirmStart}
                className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
              >
                Start Strategy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stop Confirmation Modal */}
      {confirmAction === 'stop' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-start gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  Stop Strategy?
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  This will cancel all pending orders. Open positions will remain active until their
                  take-profit targets are hit.
                </p>
                <p className="text-sm font-medium text-red-600 dark:text-red-400">
                  Are you sure you want to stop the strategy?
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setConfirmAction(null)}
                className="flex-1 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={confirmStop}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                Stop Strategy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
