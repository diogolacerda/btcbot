import { useState } from 'react'
import type { DashboardProps } from '@/../product/sections/dashboard/types'
import { PeriodSelector } from './PeriodSelector'
import { BotStatusCard } from './BotStatusCard'
import { MarketOverviewCard } from './MarketOverviewCard'
import { PerformanceMetricsCard } from './PerformanceMetricsCard'
import { PositionsTable } from './PositionsTable'
import { OrdersTable } from './OrdersTable'
import { ActivityFeed } from './ActivityFeed'
import { ConfirmDialog } from './ConfirmDialog'
import { PositionDetailsModal } from './PositionDetailsModal'

export function Dashboard({
  botStatus,
  marketData,
  performanceMetrics,
  positions,
  orders,
  activityEvents,
  selectedPeriod = 'today',
  onPeriodChange,
  onPause,
  onStop,
  onResume,
  onStart,
  onViewPosition,
  onCancelOrder,
}: DashboardProps) {
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean
    title: string
    message: string
    onConfirm: () => void
    variant?: 'danger' | 'warning' | 'default'
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  })

  const [positionModal, setPositionModal] = useState<{
    isOpen: boolean
    positionId: string | null
  }>({
    isOpen: false,
    positionId: null,
  })

  const handlePause = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Pause Bot',
      message: 'Are you sure you want to pause the trading bot? The bot will stop placing new orders until resumed.',
      onConfirm: () => onPause?.(),
      variant: 'warning',
    })
  }

  const handleStop = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Stop Bot',
      message: 'Are you sure you want to stop the trading bot? All open positions and orders will remain, but the bot will stop trading.',
      onConfirm: () => onStop?.(),
      variant: 'danger',
    })
  }

  const handleResume = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Resume Bot',
      message: 'Are you sure you want to resume the trading bot? The bot will continue grid trading.',
      onConfirm: () => onResume?.(),
      variant: 'default',
    })
  }

  const handleStart = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Start Bot',
      message: 'Are you sure you want to start the trading bot? The bot will begin grid trading based on your strategy configuration.',
      onConfirm: () => onStart?.(),
      variant: 'default',
    })
  }

  const handleViewPosition = (positionId: string) => {
    setPositionModal({
      isOpen: true,
      positionId,
    })
    onViewPosition?.(positionId)
  }

  const selectedPosition = positions.find((p) => p.id === positionModal.positionId) || null

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        {/* Header with Period Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              Dashboard
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Real-time monitoring of bot status, positions, and performance
            </p>
          </div>
          <PeriodSelector selectedPeriod={selectedPeriod} onPeriodChange={onPeriodChange} />
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <BotStatusCard
            botStatus={botStatus}
            onPause={handlePause}
            onStop={handleStop}
            onResume={handleResume}
            onStart={handleStart}
          />
          <MarketOverviewCard marketData={marketData} />
        </div>

        <div className="mb-6">
          <PerformanceMetricsCard performanceMetrics={performanceMetrics} />
        </div>

        {/* Active Trading Section */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 mb-6">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-6">
            Active Trading
          </h3>
          <div className="space-y-8">
            <PositionsTable positions={positions} onViewPosition={handleViewPosition} />
            <OrdersTable orders={orders} onCancelOrder={onCancelOrder} />
          </div>
        </div>

        {/* Activity Feed */}
        <ActivityFeed activityEvents={activityEvents} />

        {/* Dialogs and Modals */}
        <ConfirmDialog
          isOpen={confirmDialog.isOpen}
          onClose={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
          onConfirm={confirmDialog.onConfirm}
          title={confirmDialog.title}
          message={confirmDialog.message}
          variant={confirmDialog.variant}
        />

        <PositionDetailsModal
          isOpen={positionModal.isOpen}
          onClose={() => setPositionModal({ isOpen: false, positionId: null })}
          position={selectedPosition}
        />
      </div>
    </div>
  )
}
