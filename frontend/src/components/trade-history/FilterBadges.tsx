import { X } from 'lucide-react'
import type { TradeFilters } from './types'

interface FilterBadgesProps {
  filters?: TradeFilters
  onRemoveFilter?: (filterKey: keyof TradeFilters) => void
  onClearFilters?: () => void
}

export function FilterBadges({
  filters,
  onRemoveFilter,
  onClearFilters,
}: FilterBadgesProps) {
  const activeFilters: Array<{ key: keyof TradeFilters; label: string }> = []

  if (filters?.searchQuery) {
    activeFilters.push({
      key: 'searchQuery',
      label: `Search: "${filters.searchQuery}"`,
    })
  }

  if (filters?.status && filters.status !== 'all') {
    activeFilters.push({ key: 'status', label: `Status: ${filters.status}` })
  }

  if (filters?.profitFilter && filters.profitFilter !== 'all') {
    activeFilters.push({
      key: 'profitFilter',
      label: `P&L: ${filters.profitFilter === 'profitable' ? 'Profitable' : 'Losses'}`,
    })
  }

  if (filters?.entryPriceRange) {
    const { min, max } = filters.entryPriceRange
    const minLabel = min ? `$${min.toLocaleString()}` : 'Any'
    const maxLabel = max !== Infinity ? `$${max.toLocaleString()}` : 'Any'
    activeFilters.push({
      key: 'entryPriceRange',
      label: `Entry: ${minLabel} - ${maxLabel}`,
    })
  }

  if (filters?.durationRange) {
    const { min, max } = filters.durationRange
    const minLabel = min ? `${min}s` : 'Any'
    const maxLabel = max !== Infinity ? `${max}s` : 'Any'
    activeFilters.push({
      key: 'durationRange',
      label: `Duration: ${minLabel} - ${maxLabel}`,
    })
  }

  if (filters?.quantityRange) {
    const { min, max } = filters.quantityRange
    const minLabel = min ? min.toString() : 'Any'
    const maxLabel = max !== Infinity ? max.toString() : 'Any'
    activeFilters.push({
      key: 'quantityRange',
      label: `Quantity: ${minLabel} - ${maxLabel}`,
    })
  }

  if (activeFilters.length === 0) {
    return null
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-sm text-slate-600 dark:text-slate-400">
        Active filters:
      </span>

      {activeFilters.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onRemoveFilter?.(key)}
          className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 rounded-full text-sm font-medium hover:bg-emerald-200 dark:hover:bg-emerald-800 transition-colors"
        >
          {label}
          <X className="w-3 h-3" />
        </button>
      ))}

      {activeFilters.length > 1 && (
        <button
          onClick={onClearFilters}
          className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium transition-colors"
        >
          Clear all
        </button>
      )}
    </div>
  )
}
