/**
 * Period Selector Component
 *
 * Allows users to select a time period for filtering dashboard data.
 * Supports predefined periods (today, 7 days, 30 days) and custom date ranges.
 */

import { useState } from 'react'
import type { TimePeriod } from '@/types/api'

interface PeriodSelectorProps {
  value: TimePeriod
  onChange: (period: TimePeriod, startDate?: string, endDate?: string) => void
  className?: string
}

const PERIOD_OPTIONS: { value: TimePeriod; label: string }[] = [
  { value: 'today', label: 'Today' },
  { value: '7days', label: '7 Days' },
  { value: '30days', label: '30 Days' },
  { value: 'custom', label: 'Custom' },
]

export function PeriodSelector({ value, onChange, className = '' }: PeriodSelectorProps) {
  const [showDatePicker, setShowDatePicker] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const handlePeriodChange = (period: TimePeriod) => {
    if (period === 'custom') {
      setShowDatePicker(true)
    } else {
      setShowDatePicker(false)
      onChange(period)
    }
  }

  const handleCustomApply = () => {
    if (startDate && endDate) {
      onChange('custom', startDate, endDate)
      setShowDatePicker(false)
    }
  }

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      <div className="flex rounded-lg border border-border bg-muted p-1">
        {PERIOD_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => handlePeriodChange(option.value)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              value === option.value
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {showDatePicker && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-2 py-1.5 text-sm border border-border rounded-md bg-background text-foreground"
          />
          <span className="text-muted-foreground">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="px-2 py-1.5 text-sm border border-border rounded-md bg-background text-foreground"
          />
          <button
            onClick={handleCustomApply}
            disabled={!startDate || !endDate}
            className="px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  )
}

export default PeriodSelector
