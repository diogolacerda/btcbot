import { Search, SlidersHorizontal, X } from 'lucide-react'
import { useState } from 'react'
import type { TradeFilters, TradeFilterStatus, TradeProfitFilter } from './types'

interface FiltersProps {
  filters?: TradeFilters
  onFiltersChange?: (filters: TradeFilters) => void
  onSearch?: (query: string) => void
}

export function Filters({ filters, onFiltersChange, onSearch }: FiltersProps) {
  const [searchQuery, setSearchQuery] = useState(filters?.searchQuery || '')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleStatusChange = (status: TradeFilterStatus) => {
    onFiltersChange?.({ ...filters, status })
  }

  const handleProfitFilterChange = (profitFilter: TradeProfitFilter) => {
    onFiltersChange?.({ ...filters, profitFilter })
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch?.(searchQuery)
    onFiltersChange?.({ ...filters, searchQuery })
  }

  const handleEntryPriceChange = (min: string, max: string) => {
    const minValue = min ? parseFloat(min) : undefined
    const maxValue = max ? parseFloat(max) : undefined

    if (minValue !== undefined || maxValue !== undefined) {
      onFiltersChange?.({
        ...filters,
        entryPriceRange: { min: minValue || 0, max: maxValue || Infinity },
      })
    } else {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { entryPriceRange: _, ...rest } = filters || {}
      onFiltersChange?.(rest)
    }
  }

  const handleDurationChange = (min: string, max: string) => {
    const minValue = min ? parseInt(min) : undefined
    const maxValue = max ? parseInt(max) : undefined

    if (minValue !== undefined || maxValue !== undefined) {
      onFiltersChange?.({
        ...filters,
        durationRange: { min: minValue || 0, max: maxValue || Infinity },
      })
    } else {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { durationRange: _, ...rest } = filters || {}
      onFiltersChange?.(rest)
    }
  }

  const handleQuantityChange = (min: string, max: string) => {
    const minValue = min ? parseFloat(min) : undefined
    const maxValue = max ? parseFloat(max) : undefined

    if (minValue !== undefined || maxValue !== undefined) {
      onFiltersChange?.({
        ...filters,
        quantityRange: { min: minValue || 0, max: maxValue || Infinity },
      })
    } else {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { quantityRange: _, ...rest } = filters || {}
      onFiltersChange?.(rest)
    }
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
      <div className="space-y-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit}>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Search by Order ID
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search order ID or TP order ID..."
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('')
                  onSearch?.('')
                  // eslint-disable-next-line @typescript-eslint/no-unused-vars
                  const { searchQuery: _, ...rest } = filters || {}
                  onFiltersChange?.(rest)
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Status
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => handleStatusChange('all')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                (filters?.status || 'all') === 'all'
                  ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => handleStatusChange('closed')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filters?.status === 'closed'
                  ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              Closed
            </button>
            <button
              onClick={() => handleStatusChange('open')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filters?.status === 'open'
                  ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              Open
            </button>
          </div>
        </div>

        {/* Profit/Loss Filter */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Profit/Loss
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => handleProfitFilterChange('all')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                (filters?.profitFilter || 'all') === 'all'
                  ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => handleProfitFilterChange('profitable')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filters?.profitFilter === 'profitable'
                  ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              Profitable
            </button>
            <button
              onClick={() => handleProfitFilterChange('losses')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filters?.profitFilter === 'losses'
                  ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              Losses
            </button>
          </div>
        </div>

        {/* Advanced Filters Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors"
        >
          <SlidersHorizontal className="w-4 h-4" />
          {showAdvanced ? 'Hide' : 'Show'} Advanced Filters
        </button>

        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-700">
            {/* Entry Price Range */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Entry Price Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  defaultValue={filters?.entryPriceRange?.min}
                  onChange={(e) =>
                    handleEntryPriceChange(
                      e.target.value,
                      filters?.entryPriceRange?.max?.toString() || ''
                    )
                  }
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                />
                <input
                  type="number"
                  placeholder="Max"
                  defaultValue={filters?.entryPriceRange?.max}
                  onChange={(e) =>
                    handleEntryPriceChange(
                      filters?.entryPriceRange?.min?.toString() || '',
                      e.target.value
                    )
                  }
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                />
              </div>
            </div>

            {/* Duration Range */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Duration Range (seconds)
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  defaultValue={filters?.durationRange?.min}
                  onChange={(e) =>
                    handleDurationChange(
                      e.target.value,
                      filters?.durationRange?.max?.toString() || ''
                    )
                  }
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                />
                <input
                  type="number"
                  placeholder="Max"
                  defaultValue={filters?.durationRange?.max}
                  onChange={(e) =>
                    handleDurationChange(
                      filters?.durationRange?.min?.toString() || '',
                      e.target.value
                    )
                  }
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                />
              </div>
            </div>

            {/* Quantity Range */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Quantity Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  step="0.0001"
                  placeholder="Min"
                  defaultValue={filters?.quantityRange?.min}
                  onChange={(e) =>
                    handleQuantityChange(
                      e.target.value,
                      filters?.quantityRange?.max?.toString() || ''
                    )
                  }
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                />
                <input
                  type="number"
                  step="0.0001"
                  placeholder="Max"
                  defaultValue={filters?.quantityRange?.max}
                  onChange={(e) =>
                    handleQuantityChange(
                      filters?.quantityRange?.min?.toString() || '',
                      e.target.value
                    )
                  }
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:focus:ring-emerald-400"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
