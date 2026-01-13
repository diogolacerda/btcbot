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
import type { Position } from '@/types'

// Data hooks
import {
  useBotStatus,
  useMarketData,
  usePerformanceMetrics,
  usePositions,
  useActivityEvents,
  dashboardKeys,
} from '@/hooks/useDashboardData'
import { useDashboardWebSocket } from '@/hooks/useDashboardWebSocket'
import { useBotControl } from '@/hooks/useBotControl'
import { useStrategies, useMACDFilterConfig } from '@/hooks/useStrategies'

// Dashboard components
import {
  StrategyStatusCard,
  MarketOverviewCard,
  PerformanceMetricsCard,
  PositionsTable,
  ActivityFeed,
  ConfirmDialog,
  PositionDetailsModal,
} from '@/components/dashboard'

type BotAction = 'start' | 'stop' | 'pause' | 'resume' | null

export function DashboardPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()

  // Modal states
  const [confirmAction, setConfirmAction] = useState<BotAction>(null)
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)

  // Data queries
  const botStatus = useBotStatus()
  const marketData = useMarketData()

  // Fetch active strategy for StrategyStatusCard (FE-DASH-006)
  const { data: strategies } = useStrategies()
  const activeStrategy = strategies?.find(s => s.isActive)
  const { data: macdFilterConfig } = useMACDFilterConfig(
    activeStrategy?.id ?? '',
    { enabled: !!activeStrategy?.id }
  )
  const performanceMetrics = usePerformanceMetrics()
  const positions = usePositions({ limit: 20 })
  const activityEvents = useActivityEvents({ limit: 50 })

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
      queryClient.invalidateQueries({ queryKey: dashboardKeys.activity() })
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

  const handlePositionClick = useCallback((position: Position) => {
    setSelectedPosition(position)
  }, [])

  const handleClosePositionModal = useCallback(() => {
    setSelectedPosition(null)
  }, [])

  // Confirm dialog content (FE-DASH-006: Updated to strategy-centric terminology)
  const getConfirmDialogContent = () => {
    switch (confirmAction) {
      case 'start':
        return {
          title: 'Activate Strategy',
          message: 'Are you sure you want to activate this strategy? It will begin executing trades according to the configured parameters.',
          confirmLabel: 'Activate',
          variant: 'default' as const,
        }
      case 'stop':
        return {
          title: 'Stop & Cancel Grid',
          message: 'Are you sure you want to stop the bot? This will cancel all pending grid orders (LIMIT orders) and stop the strategy. Open positions and their TP orders will remain active until they hit their take-profit targets.',
          confirmLabel: 'Stop & Cancel Grid',
          variant: 'danger' as const,
        }
      case 'pause':
        return {
          title: 'Pause New Orders',
          message: 'Are you sure you want to pause new orders? The bot will stop placing new grid orders but will keep all existing LIMIT orders and positions active.',
          confirmLabel: 'Pause New Orders',
          variant: 'default' as const,
        }
      case 'resume':
        return {
          title: 'Resume Strategy',
          message: 'Are you sure you want to resume this strategy? It will continue placing orders according to the configured parameters.',
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
            {/* WebSocket Status */}
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${
                connectionState === 'connected' ? 'bg-green-500' :
                connectionState === 'connecting' || connectionState === 'reconnecting' ? 'bg-yellow-500 animate-pulse' :
                'bg-red-500'
              }`} />
              <span className="text-muted-foreground capitalize">{connectionState}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-6">
          {/* Row 1: Strategy Status (full width) */}
          <StrategyStatusCard
            data={botStatus.data}
            strategyName={activeStrategy?.name}
            strategyTimeframe={macdFilterConfig?.timeframe}
            strategySymbol={activeStrategy?.symbol}
            strategyLeverage={activeStrategy?.leverage}
            strategyOrderSize={activeStrategy?.orderSizeUsdt}
            strategyTakeProfit={activeStrategy?.takeProfitPercent}
            isLoading={botStatus.isLoading}
            isError={botStatus.isError}
            onActivate={() => handleBotAction('start')}
            onDeactivate={() => handleBotAction('stop')}
            onPause={() => handleBotAction('pause')}
            onResume={() => handleBotAction('resume')}
            isControlLoading={isControlLoading}
          />

          {/* Row 2: Market Overview & Performance (2 columns) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MarketOverviewCard
              price={marketData.price.data}
              funding={marketData.funding.data}
              macd={marketData.macd.data}
              gridRange={marketData.gridRange.data}
              isLoading={marketData.isLoading}
              isError={marketData.isError}
            />
            <PerformanceMetricsCard
              data={performanceMetrics.data}
              isLoading={performanceMetrics.isLoading}
              isError={performanceMetrics.isError}
            />
          </div>

          {/* Row 3: Open Positions (full width) */}
          <PositionsTable
            positions={positions.data?.positions}
            currentPrice={currentPrice}
            isLoading={positions.isLoading}
            isError={positions.isError}
            onPositionClick={handlePositionClick}
          />

          {/* Row 4: Activity Feed (full width) */}
          <ActivityFeed
            events={activityEvents.data?.events}
            isLoading={activityEvents.isLoading}
            isError={activityEvents.isError}
            maxItems={15}
          />
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
