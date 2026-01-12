import { useState, useRef, useEffect } from 'react'
import { Calendar, ChevronDown, Check } from 'lucide-react'
import { format } from 'date-fns'
import type { TimePeriod } from '@/../product/sections/dashboard/types'

interface PeriodSelectorProps {
  selectedPeriod?: TimePeriod
  onPeriodChange?: (period: TimePeriod, customRange?: { startDate: string; endDate: string }) => void
}

const periodLabels: Record<TimePeriod, string> = {
  today: 'Today',
  '7days': '7 Days',
  '30days': '30 Days',
  custom: 'Custom',
}

export function PeriodSelector({ selectedPeriod = 'today', onPeriodChange }: PeriodSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setShowCustomPicker(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleSelect = (period: TimePeriod) => {
    if (period === 'custom') {
      setShowCustomPicker(true)
    } else {
      onPeriodChange?.(period)
      setIsOpen(false)
      setShowCustomPicker(false)
    }
  }

  const handleApplyCustom = () => {
    if (startDate && endDate) {
      onPeriodChange?.('custom', { startDate, endDate })
      setIsOpen(false)
      setShowCustomPicker(false)
    }
  }

  const getTodayDate = () => {
    return format(new Date(), 'yyyy-MM-dd')
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors"
      >
        <Calendar className="w-4 h-4 text-slate-500 dark:text-slate-400" />
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {periodLabels[selectedPeriod]}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && !showCustomPicker && (
        <div className="absolute right-0 mt-2 w-40 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-50">
          {(Object.keys(periodLabels) as TimePeriod[]).map((period) => (
            <button
              key={period}
              onClick={() => handleSelect(period)}
              className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                period === selectedPeriod
                  ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-medium'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              {periodLabels[period]}
            </button>
          ))}
        </div>
      )}

      {isOpen && showCustomPicker && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 p-4 z-50">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            Custom Period
          </h4>

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
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-600"
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
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-600"
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => {
                setShowCustomPicker(false)
                setStartDate('')
                setEndDate('')
              }}
              className="flex-1 px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApplyCustom}
              disabled={!startDate || !endDate}
              className="flex-1 px-3 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
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
