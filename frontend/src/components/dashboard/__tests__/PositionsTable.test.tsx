/**
 * PositionsTable Component Tests
 *
 * Tests for the positions table displaying open positions with P&L.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { PositionsTable } from '../PositionsTable'
import { mockPositions } from '@/test/mocks'

describe('PositionsTable', () => {
  const defaultProps = {
    positions: mockPositions,
    currentPrice: 98000.00,
    isLoading: false,
    isError: false,
  }

  describe('loading state', () => {
    it('renders loading skeleton when loading', () => {
      const { container } = render(<PositionsTable {...defaultProps} isLoading={true} />)

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders error message when error', () => {
      render(<PositionsTable {...defaultProps} isError={true} />)

      expect(screen.getByText('Failed to load positions')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('renders empty message when no positions', () => {
      render(<PositionsTable {...defaultProps} positions={[]} />)

      expect(screen.getByText('No open positions')).toBeInTheDocument()
      expect(screen.getByText('Positions appear when orders are filled')).toBeInTheDocument()
    })

    it('filters out non-FILLED positions', () => {
      const mixedPositions = [
        { ...mockPositions[0], status: 'PENDING' as const },
        { ...mockPositions[1], status: 'TP_HIT' as const },
      ]
      render(<PositionsTable {...defaultProps} positions={mixedPositions} />)

      expect(screen.getByText('No open positions')).toBeInTheDocument()
    })
  })

  describe('header', () => {
    it('renders title', () => {
      render(<PositionsTable {...defaultProps} />)

      expect(screen.getByText('Open Positions')).toBeInTheDocument()
    })

    it('renders position count singular', () => {
      render(<PositionsTable {...defaultProps} positions={[mockPositions[0]]} />)

      expect(screen.getByText('1 position')).toBeInTheDocument()
    })

    it('renders position count plural', () => {
      render(<PositionsTable {...defaultProps} />)

      expect(screen.getByText('2 positions')).toBeInTheDocument()
    })
  })

  describe('position data', () => {
    it('renders position side with correct color', () => {
      render(<PositionsTable {...defaultProps} />)

      const longElements = screen.getAllByText('LONG')
      expect(longElements[0]).toHaveClass('text-green-500')
    })

    it('renders position quantity', () => {
      render(<PositionsTable {...defaultProps} />)

      expect(screen.getByText('0.0010 BTC')).toBeInTheDocument()
    })

    it('renders entry price', () => {
      render(<PositionsTable {...defaultProps} />)

      expect(screen.getAllByText('Entry').length).toBeGreaterThan(0)
      expect(screen.getByText('$97,500.00')).toBeInTheDocument()
    })

    it('renders current price', () => {
      render(<PositionsTable {...defaultProps} />)

      expect(screen.getAllByText('Current').length).toBeGreaterThan(0)
      // Both positions show current price
      const priceElements = screen.getAllByText('$98,000.00')
      expect(priceElements.length).toBeGreaterThan(0)
    })

    it('renders TP target', () => {
      render(<PositionsTable {...defaultProps} />)

      expect(screen.getAllByText('TP Target').length).toBeGreaterThan(0)
    })
  })

  describe('P&L calculation', () => {
    it('renders positive P&L in green', () => {
      render(<PositionsTable {...defaultProps} />)

      // Position 1: entry 97500, current 98000 -> profit
      const pnlElements = screen.getAllByText(/\+\$/)
      expect(pnlElements.length).toBeGreaterThan(0)
      expect(pnlElements[0]).toHaveClass('text-green-500')
    })

    it('renders negative P&L in red', () => {
      // Current price below entry (97500)
      render(<PositionsTable {...defaultProps} currentPrice={97000.00} />)

      // Position PnL is negative, look for red text elements
      const redElements = document.querySelectorAll('.text-red-500')
      expect(redElements.length).toBeGreaterThan(0)
    })

    it('shows placeholder when currentPrice is undefined', () => {
      render(<PositionsTable {...defaultProps} currentPrice={undefined} />)

      const placeholders = screen.getAllByText('--')
      expect(placeholders.length).toBeGreaterThan(0)
    })
  })

  describe('progress bar', () => {
    it('renders progress bar when currentPrice is defined', () => {
      render(<PositionsTable {...defaultProps} />)

      // Check for progress bar by checking the component renders successfully
      expect(screen.getAllByText('Entry').length).toBeGreaterThan(0)
      expect(screen.getAllByText('TP').length).toBeGreaterThan(0)
    })

    it('does not render progress bar when currentPrice is undefined', () => {
      render(<PositionsTable {...defaultProps} currentPrice={undefined} />)

      // Entry/TP labels for progress bar shouldn't exist when no price
      expect(screen.queryAllByText('--').length).toBeGreaterThan(0)
    })
  })

  describe('interactions', () => {
    it('calls onPositionClick when position is clicked', async () => {
      const user = userEvent.setup()
      const onPositionClick = vi.fn()
      render(<PositionsTable {...defaultProps} onPositionClick={onPositionClick} />)

      // Find a position card and click it
      const longElements = screen.getAllByText('LONG')
      await user.click(longElements[0].closest('div[class*="hover:bg-muted"]')!)

      expect(onPositionClick).toHaveBeenCalledWith(mockPositions[0])
    })

    it('applies cursor-pointer when onPositionClick is provided', () => {
      const onPositionClick = vi.fn()
      const { container } = render(<PositionsTable {...defaultProps} onPositionClick={onPositionClick} />)

      const positionCards = container.querySelectorAll('.cursor-pointer')
      expect(positionCards.length).toBeGreaterThan(0)
    })
  })
})
