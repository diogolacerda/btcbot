import { Calendar, Check, ChevronDown, X } from 'lucide-react'
import { useState } from 'react'
import type { TimePeriod } from './types'

interface PeriodSelectorProps {
  selectedPeriod?: TimePeriod
  customDateRange?: { startDate: string; endDate: string }
  onPeriodChange?: (
    period: TimePeriod,
    customRange?: { startDate: string; endDate: string }
  ) => void
}

export function PeriodSelector({
  selectedPeriod = 'today',
  customDateRange,
  onPeriodChange,
}: PeriodSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const [startDate, setStartDate] = useState(customDateRange?.startDate || '')
  const [endDate, setEndDate] = useState(customDateRange?.endDate || '')

  const periods: Array<{ value: TimePeriod; label: string }> = [
    { value: 'today', label: 'Today' },
    { value: '7days', label: '7 Days' },
    { value: '30days', label: '30 Days' },
    { value: 'custom', label: 'Custom' },
  ]

  const selectedLabel =
    selectedPeriod === 'custom' && customDateRange
      ? `${formatDate(customDateRange.startDate)} - ${formatDate(customDateRange.endDate)}`
      : periods.find((p) => p.value === selectedPeriod)?.label || 'Today'

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  function getTodayDate() {
    return new Date().toISOString().split('T')[0]
  }

  const handlePeriodSelect = (period: TimePeriod) => {
    if (period === 'custom') {
      setShowCustomPicker(true)
    } else {
      setShowCustomPicker(false)
      setIsOpen(false)
      onPeriodChange?.(period)
    }
  }

  const handleApplyCustom = () => {
    if (startDate && endDate) {
      setShowCustomPicker(false)
      setIsOpen(false)
      onPeriodChange?.('custom', { startDate, endDate })
    }
  }

  const handleCancelCustom = () => {
    setShowCustomPicker(false)
    setStartDate(customDateRange?.startDate || '')
    setEndDate(customDateRange?.endDate || '')
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
      >
        <Calendar className="w-4 h-4" />
        <span className="text-sm font-medium">{selectedLabel}</span>
        <ChevronDown className="w-4 h-4" />
      </button>

      {isOpen && !showCustomPicker && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-50">
          {periods.map((period) => (
            <button
              key={period.value}
              onClick={() => handlePeriodSelect(period.value)}
              className={`w-full px-4 py-2 text-left text-sm transition-colors ${
                selectedPeriod === period.value
                  ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 font-medium'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      )}

      {isOpen && showCustomPicker && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 p-4 z-50">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Custom Period
            </h4>
            <button
              onClick={handleCancelCustom}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                max={endDate || getTodayDate()}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                min={startDate}
                max={getTodayDate()}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={handleCancelCustom}
              className="flex-1 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleApplyCustom}
              disabled={!startDate || !endDate}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check className="w-4 h-4" />
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
