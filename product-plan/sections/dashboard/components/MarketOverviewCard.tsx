import { TrendingUp, TrendingDown } from 'lucide-react'
import type { MarketData } from '@/../product/sections/dashboard/types'

interface MarketOverviewCardProps {
  marketData: MarketData
}

export function MarketOverviewCard({ marketData }: MarketOverviewCardProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price)
  }

  const formatPercent = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const isPriceUp = marketData.priceChange24h > 0

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-4">
        Market Overview
      </h3>

      <div className="space-y-4">
        {/* BTC Price */}
        <div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold text-slate-900 dark:text-slate-100 font-mono">
              {formatPrice(marketData.btcPrice)}
            </span>
            <div
              className={`flex items-center gap-1 px-2 py-1 rounded ${
                isPriceUp
                  ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                  : 'bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300'
              }`}
            >
              {isPriceUp ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              <span className="text-sm font-medium">{formatPercent(marketData.priceChange24h)}</span>
            </div>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">BTC/USDT • 24h</p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-200 dark:border-slate-700">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Funding Rate</p>
            <p className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono">
              {formatPercent(marketData.fundingRate)}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {marketData.fundingInterval}
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">MACD Signal</p>
            <div
              className={`inline-flex items-center gap-1 px-2 py-1 rounded ${
                marketData.macdSignal === 'bullish'
                  ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                  : 'bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300'
              }`}
            >
              <span className="text-lg font-bold">
                {marketData.macdSignal === 'bullish' ? '🟢' : '🔴'}
              </span>
              <span className="text-sm font-medium capitalize">{marketData.macdSignal}</span>
            </div>
          </div>

          <div className="col-span-2">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Grid Range</p>
            <p className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono">
              {formatPrice(marketData.gridRangeLow)} - {formatPrice(marketData.gridRangeHigh)}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              ±{(((marketData.gridRangeHigh - marketData.gridRangeLow) / 2 / marketData.btcPrice) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
