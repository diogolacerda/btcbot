/**
 * BotStatusCard Component Tests
 *
 * Tests for the bot status display and control buttons.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { BotStatusCard } from '../BotStatusCard'
import { mockBotStatus, mockBotStatusStopped } from '@/test/mocks'
import type { BotStatusResponse } from '@/types/api'

describe('BotStatusCard', () => {
  const defaultProps = {
    data: mockBotStatus,
    isLoading: false,
    isError: false,
  }

  describe('loading state', () => {
    it('renders loading skeleton when loading', () => {
      const { container } = render(<BotStatusCard {...defaultProps} isLoading={true} />)

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
      expect(screen.queryByText('Bot Status')).not.toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders error message when error', () => {
      render(<BotStatusCard {...defaultProps} isError={true} />)

      expect(screen.getByText('Failed to load bot status')).toBeInTheDocument()
    })

    it('renders error message when data is undefined', () => {
      render(<BotStatusCard {...defaultProps} data={undefined} />)

      expect(screen.getByText('Failed to load bot status')).toBeInTheDocument()
    })
  })

  describe('data display', () => {
    it('renders bot status title', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByText('Bot Status')).toBeInTheDocument()
    })

    it('renders state badge with correct label', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('renders state description', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByText('Grid is active and placing orders')).toBeInTheDocument()
    })

    it('renders MACD values', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByText('MACD Line')).toBeInTheDocument()
      expect(screen.getByText('125.50')).toBeInTheDocument()
      expect(screen.getByText('Histogram')).toBeInTheDocument()
      expect(screen.getByText('45.20')).toBeInTheDocument()
    })

    it('renders order statistics', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByText('Pending Orders')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('Open Positions')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('renders total P&L with positive value', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByText('Total P&L')).toBeInTheDocument()
      expect(screen.getByText('$1250.75')).toBeInTheDocument()
    })

    it('renders negative P&L with red color', () => {
      const negativePnlData: BotStatusResponse = {
        ...mockBotStatus,
        orders: { ...mockBotStatus.orders, totalPnl: -500.25 },
      }
      render(<BotStatusCard {...defaultProps} data={negativePnlData} />)

      const pnlElement = screen.getByText('$-500.25')
      expect(pnlElement).toHaveClass('text-red-500')
    })
  })

  describe('state badges', () => {
    const states: Array<{ state: BotStatusResponse['state']; label: string }> = [
      { state: 'INACTIVE', label: 'Inactive' },
      { state: 'WAIT', label: 'Waiting' },
      { state: 'ACTIVATE', label: 'Activating' },
      { state: 'ACTIVE', label: 'Active' },
      { state: 'PAUSE', label: 'Paused' },
    ]

    states.forEach(({ state, label }) => {
      it(`renders ${label} badge for ${state} state`, () => {
        const data: BotStatusResponse = { ...mockBotStatus, state }
        render(<BotStatusCard {...defaultProps} data={data} />)

        expect(screen.getByText(label)).toBeInTheDocument()
      })
    })
  })

  describe('error indicators', () => {
    it('does not show error indicators when no errors', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.queryByText('Margin Error')).not.toBeInTheDocument()
      expect(screen.queryByText('Rate Limited')).not.toBeInTheDocument()
    })

    it('shows margin error indicator', () => {
      const data: BotStatusResponse = {
        ...mockBotStatus,
        errors: { marginError: true, rateLimited: false },
      }
      render(<BotStatusCard {...defaultProps} data={data} />)

      expect(screen.getByText('Margin Error')).toBeInTheDocument()
    })

    it('shows rate limited indicator', () => {
      const data: BotStatusResponse = {
        ...mockBotStatus,
        errors: { marginError: false, rateLimited: true },
      }
      render(<BotStatusCard {...defaultProps} data={data} />)

      expect(screen.getByText('Rate Limited')).toBeInTheDocument()
    })

    it('shows both error indicators', () => {
      const data: BotStatusResponse = {
        ...mockBotStatus,
        errors: { marginError: true, rateLimited: true },
      }
      render(<BotStatusCard {...defaultProps} data={data} />)

      expect(screen.getByText('Margin Error')).toBeInTheDocument()
      expect(screen.getByText('Rate Limited')).toBeInTheDocument()
    })
  })

  describe('control buttons - running state', () => {
    it('shows Pause and Stop buttons when running and not paused', () => {
      render(<BotStatusCard {...defaultProps} />)

      expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Stop' })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Start Bot' })).not.toBeInTheDocument()
    })

    it('shows Resume and Stop buttons when paused', () => {
      const pausedData: BotStatusResponse = {
        ...mockBotStatus,
        state: 'PAUSE',
      }
      render(<BotStatusCard {...defaultProps} data={pausedData} />)

      expect(screen.getByRole('button', { name: 'Resume' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Stop' })).toBeInTheDocument()
    })

    it('calls onPause when Pause is clicked', async () => {
      const user = userEvent.setup()
      const onPause = vi.fn()
      render(<BotStatusCard {...defaultProps} onPause={onPause} />)

      await user.click(screen.getByRole('button', { name: 'Pause' }))

      expect(onPause).toHaveBeenCalledTimes(1)
    })

    it('calls onStop when Stop is clicked', async () => {
      const user = userEvent.setup()
      const onStop = vi.fn()
      render(<BotStatusCard {...defaultProps} onStop={onStop} />)

      await user.click(screen.getByRole('button', { name: 'Stop' }))

      expect(onStop).toHaveBeenCalledTimes(1)
    })

    it('calls onResume when Resume is clicked', async () => {
      const user = userEvent.setup()
      const onResume = vi.fn()
      const pausedData: BotStatusResponse = { ...mockBotStatus, state: 'PAUSE' }
      render(<BotStatusCard {...defaultProps} data={pausedData} onResume={onResume} />)

      await user.click(screen.getByRole('button', { name: 'Resume' }))

      expect(onResume).toHaveBeenCalledTimes(1)
    })
  })

  describe('control buttons - stopped state', () => {
    it('shows Start Bot button when stopped', () => {
      render(<BotStatusCard {...defaultProps} data={mockBotStatusStopped} />)

      expect(screen.getByRole('button', { name: 'Start Bot' })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Pause' })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Stop' })).not.toBeInTheDocument()
    })

    it('calls onStart when Start Bot is clicked', async () => {
      const user = userEvent.setup()
      const onStart = vi.fn()
      render(<BotStatusCard {...defaultProps} data={mockBotStatusStopped} onStart={onStart} />)

      await user.click(screen.getByRole('button', { name: 'Start Bot' }))

      expect(onStart).toHaveBeenCalledTimes(1)
    })
  })

  describe('loading state for controls', () => {
    it('disables all buttons when control is loading', () => {
      render(<BotStatusCard {...defaultProps} isControlLoading={true} />)

      const pauseButton = screen.getByRole('button', { name: 'Pause' })
      const stopButton = screen.getByRole('button', { name: 'Stop' })

      expect(pauseButton).toBeDisabled()
      expect(stopButton).toBeDisabled()
    })

    it('disables Start Bot button when control is loading', () => {
      render(
        <BotStatusCard
          {...defaultProps}
          data={mockBotStatusStopped}
          isControlLoading={true}
        />
      )

      expect(screen.getByRole('button', { name: 'Start Bot' })).toBeDisabled()
    })
  })
})
