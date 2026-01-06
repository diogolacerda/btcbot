/**
 * ActivityFeed Component Tests
 *
 * Tests for the activity feed displaying trading events.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ActivityFeed } from '../ActivityFeed'
import { mockActivityEvents } from '@/test/mocks'

describe('ActivityFeed', () => {
  const defaultProps = {
    events: mockActivityEvents,
    isLoading: false,
    isError: false,
  }

  // Mock date for consistent timestamp testing
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-06T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('loading state', () => {
    it('renders loading skeleton when loading', () => {
      const { container } = render(<ActivityFeed {...defaultProps} isLoading={true} />)

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders error message when error', () => {
      render(<ActivityFeed {...defaultProps} isError={true} />)

      expect(screen.getByText('Failed to load activity')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('renders empty message when no events', () => {
      render(<ActivityFeed {...defaultProps} events={[]} />)

      expect(screen.getByText('No recent activity')).toBeInTheDocument()
      expect(screen.getByText('Events will appear here as they occur')).toBeInTheDocument()
    })

    it('renders empty message when events is undefined', () => {
      render(<ActivityFeed {...defaultProps} events={undefined} />)

      expect(screen.getByText('No recent activity')).toBeInTheDocument()
    })
  })

  describe('header', () => {
    it('renders title', () => {
      render(<ActivityFeed {...defaultProps} />)

      expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    })
  })

  describe('event display', () => {
    it('renders event labels', () => {
      render(<ActivityFeed {...defaultProps} />)

      expect(screen.getByText('Order Filled')).toBeInTheDocument()
      expect(screen.getByText('Trade Closed')).toBeInTheDocument()
      expect(screen.getByText('Cycle Activated')).toBeInTheDocument()
      expect(screen.getByText('Bot Started')).toBeInTheDocument()
      expect(screen.getByText('Error Occurred')).toBeInTheDocument()
    })

    it('renders event descriptions', () => {
      render(<ActivityFeed {...defaultProps} />)

      expect(screen.getByText('Order filled at $98,000.00')).toBeInTheDocument()
      expect(screen.getByText('Trade closed with +$25.50 profit')).toBeInTheDocument()
      expect(screen.getByText('Trading cycle activated')).toBeInTheDocument()
    })

    it('renders event icons', () => {
      const { container } = render(<ActivityFeed {...defaultProps} />)

      // Check that icon containers exist
      const iconContainers = container.querySelectorAll('.rounded-full.flex.items-center')
      expect(iconContainers.length).toBeGreaterThan(0)
    })
  })

  describe('timestamps', () => {
    it('formats recent timestamps correctly', () => {
      render(<ActivityFeed {...defaultProps} />)

      // Event at 11:30 is 30 minutes ago
      expect(screen.getByText('30m ago')).toBeInTheDocument()
      // Event at 11:00 is 1 hour ago
      expect(screen.getByText('1h ago')).toBeInTheDocument()
    })

    it('formats older timestamps as hours', () => {
      render(<ActivityFeed {...defaultProps} />)

      // Event at 10:00 is 2 hours ago
      expect(screen.getByText('2h ago')).toBeInTheDocument()
      // Event at 09:00 is 3 hours ago
      expect(screen.getByText('3h ago')).toBeInTheDocument()
    })
  })

  describe('event data display', () => {
    it('renders event data when present', () => {
      render(<ActivityFeed {...defaultProps} />)

      // ORDER_FILLED event has eventData { price: 98000, side: 'LONG' }
      expect(screen.getByText('price:')).toBeInTheDocument()
      expect(screen.getByText('98000')).toBeInTheDocument()
      expect(screen.getByText('side:')).toBeInTheDocument()
    })
  })

  describe('color coding', () => {
    it('applies correct color for ORDER_FILLED', () => {
      render(<ActivityFeed {...defaultProps} />)

      const orderFilledLabel = screen.getByText('Order Filled')
      expect(orderFilledLabel).toHaveClass('text-blue-500')
    })

    it('applies correct color for TRADE_CLOSED', () => {
      render(<ActivityFeed {...defaultProps} />)

      const tradeClosedLabel = screen.getByText('Trade Closed')
      expect(tradeClosedLabel).toHaveClass('text-green-500')
    })

    it('applies correct color for ERROR_OCCURRED', () => {
      render(<ActivityFeed {...defaultProps} />)

      const errorLabel = screen.getByText('Error Occurred')
      expect(errorLabel).toHaveClass('text-red-500')
    })
  })

  describe('maxItems prop', () => {
    it('limits displayed events to maxItems', () => {
      render(<ActivityFeed {...defaultProps} maxItems={2} />)

      // Should only show 2 events
      const eventLabels = screen.getAllByText(/Filled|Closed|Activated|Started|Occurred/)
      expect(eventLabels.length).toBe(2)
    })

    it('shows pagination message when events exceed maxItems', () => {
      render(<ActivityFeed {...defaultProps} maxItems={2} />)

      expect(screen.getByText(/Showing 2 of 5 events/)).toBeInTheDocument()
    })

    it('does not show pagination when all events are displayed', () => {
      render(<ActivityFeed {...defaultProps} />)

      expect(screen.queryByText(/Showing.*of.*events/)).not.toBeInTheDocument()
    })
  })
})
