import { useState } from 'react'
import { PeriodSelector } from './PeriodSelector'
import { PerformanceCards } from './PerformanceCards'
import { PnlChart } from './PnlChart'
import { Filters } from './Filters'
import { FilterBadges } from './FilterBadges'
import { TradesTable } from './TradesTable'
import { TradeDetailsModal } from './TradeDetailsModal'
import type { TradeHistoryProps, Trade } from '@/../product/sections/trade-history/types'

export function TradeHistory({
  performanceMetrics,
  trades,
  cumulativePnlData,
  filters,
  sortConfig,
  currentPage = 1,
  tradesPerPage = 50,
  onPeriodChange,
  onFiltersChange,
  onSortChange,
  onViewTradeDetails,
  onSearch,
  onClearFilters,
  onRemoveFilter,
  onPageChange,
}: TradeHistoryProps) {
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  // Calculate pagination
  const totalTrades = trades.length
  const totalPages = Math.ceil(totalTrades / tradesPerPage)
  const startIndex = (currentPage - 1) * tradesPerPage
  const endIndex = startIndex + tradesPerPage
  const currentTrades = trades.slice(startIndex, endIndex)

  const handleViewDetails = (tradeId: string) => {
    const trade = trades.find((t) => t.id === tradeId)
    if (trade) {
      setSelectedTrade(trade)
      onViewTradeDetails?.(tradeId)
    }
  }

  const handleCloseModal = () => {
    setSelectedTrade(null)
  }

  const handlePageChange = (page: number) => {
    onPageChange?.(page)
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Trade History
        </h1>
        <PeriodSelector
          selectedPeriod={filters?.period}
          customDateRange={filters?.customDateRange}
          onPeriodChange={onPeriodChange}
        />
      </div>

      {/* Performance Cards */}
      <PerformanceCards performanceMetrics={performanceMetrics} />

      {/* Cumulative P&L Chart */}
      <PnlChart cumulativePnlData={cumulativePnlData} />

      {/* Filters Section */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Filters Panel - Desktop Sidebar */}
        <div className="hidden lg:block lg:w-80 flex-shrink-0">
          <Filters filters={filters} onFiltersChange={onFiltersChange} onSearch={onSearch} />
        </div>

        {/* Main Content */}
        <div className="flex-1 space-y-4">
          {/* Mobile Filter Toggle */}
          <div className="lg:hidden">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="w-full px-4 py-2 bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 rounded-lg font-medium hover:bg-emerald-200 dark:hover:bg-emerald-800 transition-colors"
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>

          {/* Mobile Filters Panel */}
          {showFilters && (
            <div className="lg:hidden">
              <Filters filters={filters} onFiltersChange={onFiltersChange} onSearch={onSearch} />
            </div>
          )}

          {/* Active Filter Badges */}
          {filters && (
            <FilterBadges
              filters={filters}
              onRemoveFilter={onRemoveFilter}
              onClearFilters={onClearFilters}
            />
          )}

          {/* Trades Count */}
          <div className="text-sm text-slate-600 dark:text-slate-400">
            Showing {startIndex + 1}-{Math.min(endIndex, totalTrades)} of {totalTrades} trades
          </div>

          {/* Trades Table */}
          {currentTrades.length > 0 ? (
            <TradesTable
              trades={currentTrades}
              sortConfig={sortConfig}
              onSort={onSortChange}
              onViewDetails={handleViewDetails}
            />
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-12 text-center">
              <p className="text-slate-600 dark:text-slate-400 mb-2">No trades found</p>
              <p className="text-sm text-slate-500 dark:text-slate-500">
                Try adjusting your filters to see more results
              </p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                  // Show first page, last page, current page, and pages around current
                  const showPage =
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)

                  if (!showPage) {
                    // Show ellipsis for gaps
                    if (page === currentPage - 2 || page === currentPage + 2) {
                      return (
                        <span
                          key={page}
                          className="px-3 py-2 text-slate-500 dark:text-slate-400"
                        >
                          ...
                        </span>
                      )
                    }
                    return null
                  }

                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-4 py-2 rounded-lg transition-colors ${
                        page === currentPage
                          ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 font-medium'
                          : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                      }`}
                    >
                      {page}
                    </button>
                  )
                })}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Trade Details Modal */}
      <TradeDetailsModal trade={selectedTrade} onClose={handleCloseModal} />
    </div>
  )
}
