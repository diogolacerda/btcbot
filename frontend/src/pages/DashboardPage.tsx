/**
 * Dashboard Page (FE-DASH-003)
 *
 * Main trading dashboard integrating all dashboard components with real data.
 * Features: bot controls, market overview, performance metrics, positions,
 * orders, activity feed, and real-time WebSocket updates.
 */

import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import type { TimePeriod, OrderSchema } from '@/types/api'

// Data hooks
import {
  useBotStatus,
  useMarketData,
  usePerformanceMetrics,
  useOrders,
  usePositions,
  useActivityEvents,
  dashboardKeys,
} from '@/hooks/useDashboardData'
import { useDashboardWebSocket } from '@/hooks/useDashboardWebSocket'
import { useBotControl } from '@/hooks/useBotControl'

// Dashboard components
import {
  PeriodSelector,
  BotStatusCard,
  MarketOverviewCard,
  PerformanceMetricsCard,
  PositionsTable,
  OrdersTable,
  ActivityFeed,
  ConfirmDialog,
  PositionDetailsModal,
} from '@/components/dashboard'

type BotAction = 'start' | 'stop' | 'pause' | 'resume' | null

export function DashboardPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()

  // Period selection state
  const [period, setPeriod] = useState<TimePeriod>('today')
  const [customDates, setCustomDates] = useState<{ start?: string; end?: string }>({})

  // Modal states
  const [confirmAction, setConfirmAction] = useState<BotAction>(null)
  const [selectedPosition, setSelectedPosition] = useState<OrderSchema | null>(null)

  // Data queries
  const botStatus = useBotStatus()
  const marketData = useMarketData()
  const performanceMetrics = usePerformanceMetrics({
    period,
    startDate: customDates.start,
    endDate: customDates.end,
  })
  const orders = useOrders({ limit: 50 })
  const positions = usePositions({ limit: 20 })
  const activityEvents = useActivityEvents({
    period,
    startDate: customDates.start,
    endDate: customDates.end,
    limit: 50,
  })

  // WebSocket for real-time updates
  const { connectionState } = useDashboardWebSocket({
    enabled: true,
    onBotStatus: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.botStatus() })
    },
    onPositionUpdate: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.positions() })
    },
    onOrderUpdate: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.orders() })
    },
    onPriceUpdate: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.price() })
    },
    onActivityEvent: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.activity(period) })
    },
  })

  // Bot control mutations with notifications (FE-DASH-004)
  const {
    startBot,
    stopBot,
    pauseBot,
    resumeBot,
    isPending: isControlLoading,
  } = useBotControl()

  // Handlers
  const handlePeriodChange = useCallback((newPeriod: TimePeriod, startDate?: string, endDate?: string) => {
    setPeriod(newPeriod)
    if (newPeriod === 'custom' && startDate && endDate) {
      setCustomDates({ start: startDate, end: endDate })
    } else {
      setCustomDates({})
    }
  }, [])

  const handleBotAction = useCallback((action: BotAction) => {
    setConfirmAction(action)
  }, [])

  const handleConfirmAction = useCallback(() => {
    switch (confirmAction) {
      case 'start':
        startBot.mutate()
        break
      case 'stop':
        stopBot.mutate()
        break
      case 'pause':
        pauseBot.mutate()
        break
      case 'resume':
        resumeBot.mutate()
        break
    }
    setConfirmAction(null)
  }, [confirmAction, startBot, stopBot, pauseBot, resumeBot])

  const handleCancelAction = useCallback(() => {
    setConfirmAction(null)
  }, [])

  const handlePositionClick = useCallback((position: OrderSchema) => {
    setSelectedPosition(position)
  }, [])

  const handleClosePositionModal = useCallback(() => {
    setSelectedPosition(null)
  }, [])

  // Confirm dialog content
  const getConfirmDialogContent = () => {
    switch (confirmAction) {
      case 'start':
        return {
          title: 'Start Bot',
          message: 'Are you sure you want to start the trading bot? It will begin executing trades according to the configured strategy.',
          confirmLabel: 'Start',
          variant: 'default' as const,
        }
      case 'stop':
        return {
          title: 'Stop Bot',
          message: 'Are you sure you want to stop the bot? This will cancel all pending orders and stop new order placement. Open positions will remain until TP is hit.',
          confirmLabel: 'Stop',
          variant: 'danger' as const,
        }
      case 'pause':
        return {
          title: 'Pause Bot',
          message: 'Are you sure you want to pause the bot? It will stop placing new orders but keep existing positions and TP orders active.',
          confirmLabel: 'Pause',
          variant: 'default' as const,
        }
      case 'resume':
        return {
          title: 'Resume Bot',
          message: 'Are you sure you want to resume the trading bot? It will continue placing orders according to the configured strategy.',
          confirmLabel: 'Resume',
          variant: 'default' as const,
        }
      default:
        return { title: '', message: '', confirmLabel: '', variant: 'default' as const }
    }
  }

  const dialogContent = getConfirmDialogContent()
  const currentPrice = marketData.price.data?.price

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Trading Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Welcome back, {user?.name || user?.email}
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* WebSocket Status */}
              <div className="flex items-center gap-2 text-sm">
                <div className={`w-2 h-2 rounded-full ${
                  connectionState === 'connected' ? 'bg-green-500' :
                  connectionState === 'connecting' || connectionState === 'reconnecting' ? 'bg-yellow-500 animate-pulse' :
                  'bg-red-500'
                }`} />
                <span className="text-muted-foreground capitalize">{connectionState}</span>
              </div>
              <PeriodSelector value={period} onChange={handlePeriodChange} />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Bot Status & Market Overview */}
          <div className="lg:col-span-1 space-y-6">
            <BotStatusCard
              data={botStatus.data}
              isLoading={botStatus.isLoading}
              isError={botStatus.isError}
              onStart={() => handleBotAction('start')}
              onStop={() => handleBotAction('stop')}
              onPause={() => handleBotAction('pause')}
              onResume={() => handleBotAction('resume')}
              isControlLoading={isControlLoading}
            />
            <MarketOverviewCard
              price={marketData.price.data}
              funding={marketData.funding.data}
              macd={marketData.macd.data}
              gridRange={marketData.gridRange.data}
              isLoading={marketData.isLoading}
              isError={marketData.isError}
            />
          </div>

          {/* Center Column - Performance & Positions */}
          <div className="lg:col-span-1 space-y-6">
            <PerformanceMetricsCard
              data={performanceMetrics.data}
              isLoading={performanceMetrics.isLoading}
              isError={performanceMetrics.isError}
            />
            <PositionsTable
              positions={positions.data?.orders}
              currentPrice={currentPrice}
              isLoading={positions.isLoading}
              isError={positions.isError}
              onPositionClick={handlePositionClick}
            />
          </div>

          {/* Right Column - Orders & Activity */}
          <div className="lg:col-span-1 space-y-6">
            <OrdersTable
              data={orders.data}
              isLoading={orders.isLoading}
              isError={orders.isError}
              onOrderClick={handlePositionClick}
            />
            <ActivityFeed
              events={activityEvents.data?.events}
              isLoading={activityEvents.isLoading}
              isError={activityEvents.isError}
              maxItems={15}
            />
          </div>
        </div>
      </main>

      {/* Confirm Dialog */}
      <ConfirmDialog
        isOpen={confirmAction !== null}
        title={dialogContent.title}
        message={dialogContent.message}
        confirmLabel={dialogContent.confirmLabel}
        variant={dialogContent.variant}
        onConfirm={handleConfirmAction}
        onCancel={handleCancelAction}
      />

      {/* Position Details Modal */}
      <PositionDetailsModal
        position={selectedPosition}
        currentPrice={currentPrice}
        isOpen={selectedPosition !== null}
        onClose={handleClosePositionModal}
      />
    </div>
  )
}

export default DashboardPage
