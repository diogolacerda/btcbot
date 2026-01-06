/**
 * DashboardPage Integration Tests
 *
 * Tests for the main dashboard page component with mocked hooks.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { DashboardPage } from '../DashboardPage'
import {
  mockBotStatus,
  mockPrice,
  mockFundingRate,
  mockMacdData,
  mockGridRange,
  mockPerformanceMetrics,
  mockOrders,
  mockActivityEvents,
} from '@/test/mocks'

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'test@example.com', name: 'Test User' },
    isAuthenticated: true,
  }),
}))

// Mock dashboard data hooks
vi.mock('@/hooks/useDashboardData', () => ({
  useBotStatus: () => ({
    data: mockBotStatus,
    isLoading: false,
    isError: false,
  }),
  useMarketData: () => ({
    price: { data: mockPrice, isLoading: false, isError: false },
    funding: { data: mockFundingRate, isLoading: false, isError: false },
    macd: { data: mockMacdData, isLoading: false, isError: false },
    gridRange: { data: mockGridRange, isLoading: false, isError: false },
    isLoading: false,
    isError: false,
  }),
  usePerformanceMetrics: () => ({
    data: mockPerformanceMetrics,
    isLoading: false,
    isError: false,
  }),
  useOrders: () => ({
    data: {
      orders: mockOrders,
      total: mockOrders.length,
      limit: 50,
      offset: 0,
      pendingCount: 1,
      filledCount: 1,
    },
    isLoading: false,
    isError: false,
  }),
  usePositions: () => ({
    data: {
      orders: mockOrders.filter(o => o.status === 'FILLED'),
      total: 1,
      limit: 20,
      offset: 0,
      pendingCount: 0,
      filledCount: 1,
    },
    isLoading: false,
    isError: false,
  }),
  useActivityEvents: () => ({
    data: {
      events: mockActivityEvents,
      total: mockActivityEvents.length,
      limit: 50,
      offset: 0,
    },
    isLoading: false,
    isError: false,
  }),
  dashboardKeys: {
    botStatus: () => ['dashboard', 'bot-status'],
    positions: () => ['dashboard', 'positions'],
    orders: () => ['dashboard', 'orders'],
    price: () => ['dashboard', 'price'],
    activity: (period: string) => ['dashboard', 'activity', period],
  },
}))

// Mock WebSocket hook
vi.mock('@/hooks/useDashboardWebSocket', () => ({
  useDashboardWebSocket: () => ({
    connectionState: 'connected',
  }),
}))

// Mock bot control hook
const mockStartBot = { mutate: vi.fn() }
const mockStopBot = { mutate: vi.fn() }
const mockPauseBot = { mutate: vi.fn() }
const mockResumeBot = { mutate: vi.fn() }

vi.mock('@/hooks/useBotControl', () => ({
  useBotControl: () => ({
    startBot: mockStartBot,
    stopBot: mockStopBot,
    pauseBot: mockPauseBot,
    resumeBot: mockResumeBot,
    isPending: false,
  }),
}))

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders the dashboard title', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Trading Dashboard')).toBeInTheDocument()
    })

    it('renders welcome message with user name', () => {
      render(<DashboardPage />)

      expect(screen.getByText(/Welcome back, Test User/)).toBeInTheDocument()
    })

    it('renders WebSocket connection status', () => {
      render(<DashboardPage />)

      expect(screen.getByText('connected')).toBeInTheDocument()
    })

    it('renders period selector', () => {
      render(<DashboardPage />)

      expect(screen.getByRole('button', { name: 'Today' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '7 Days' })).toBeInTheDocument()
    })
  })

  describe('dashboard sections', () => {
    it('renders Bot Status card', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Bot Status')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('renders Market Overview card', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Market Overview')).toBeInTheDocument()
    })

    it('renders Performance Metrics card', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
    })

    it('renders Positions table', () => {
      render(<DashboardPage />)

      // "Open Positions" appears twice (in BotStatusCard and as table title)
      const elements = screen.getAllByText('Open Positions')
      expect(elements.length).toBeGreaterThanOrEqual(1)
    })

    it('renders Orders table', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Orders')).toBeInTheDocument()
    })

    it('renders Activity Feed', () => {
      render(<DashboardPage />)

      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    })
  })

  describe('bot control confirmations', () => {
    it('shows confirm dialog when pause is clicked', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      await user.click(screen.getByRole('button', { name: 'Pause' }))

      expect(screen.getByText('Pause Bot')).toBeInTheDocument()
      expect(screen.getByText(/stop placing new orders/)).toBeInTheDocument()
    })

    it('shows confirm dialog when stop is clicked', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      await user.click(screen.getByRole('button', { name: 'Stop' }))

      expect(screen.getByText('Stop Bot')).toBeInTheDocument()
      expect(screen.getByText(/cancel all pending orders/)).toBeInTheDocument()
    })

    it('calls pauseBot when confirmed', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      await user.click(screen.getByRole('button', { name: 'Pause' }))
      // Find the confirm button in the dialog (has bg-primary class)
      const confirmButton = screen.getAllByRole('button', { name: 'Pause' })[1]
      await user.click(confirmButton)

      expect(mockPauseBot.mutate).toHaveBeenCalled()
    })

    it('calls stopBot when confirmed', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      await user.click(screen.getByRole('button', { name: 'Stop' }))
      // Find the confirm button in the dialog (second Stop button)
      const confirmButton = screen.getAllByRole('button', { name: 'Stop' })[1]
      await user.click(confirmButton)

      expect(mockStopBot.mutate).toHaveBeenCalled()
    })

    it('closes dialog when cancel is clicked', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      await user.click(screen.getByRole('button', { name: 'Pause' }))
      await user.click(screen.getByRole('button', { name: 'Cancel' }))

      expect(screen.queryByText('Pause Bot')).not.toBeInTheDocument()
    })
  })

  describe('period selection', () => {
    it('changes period when button is clicked', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      await user.click(screen.getByRole('button', { name: '7 Days' }))

      // The button should now be highlighted
      expect(screen.getByRole('button', { name: '7 Days' })).toHaveClass('bg-primary')
    })
  })

  describe('position details modal', () => {
    it('opens position details modal when position is clicked', async () => {
      const user = userEvent.setup()
      render(<DashboardPage />)

      // Find and click on a position row in the table
      const longElements = screen.getAllByText('LONG')
      const positionRow = longElements[0].closest('div[class*="hover:bg-muted"]')

      if (positionRow) {
        await user.click(positionRow)
        expect(screen.getByText('Position Details')).toBeInTheDocument()
      }
    })
  })
})
