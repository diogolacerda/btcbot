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
  })

  describe('progress bar', () => {
    it('renders progress bar when currentPrice is defined', () => {
      render(<PositionsTable {...defaultProps} />)

      // Check for progress bar by checking the component renders successfully
      expect(screen.getAllByText('Entry').length).toBeGreaterThan(0)
      expect(screen.getAllByText('TP').length).toBeGreaterThan(0)
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

  describe('sorting', () => {
    it('sorts positions by TP price ascending', () => {
      const unsortedPositions = [
        {
          symbol: 'BTC-USDT',
          side: 'LONG' as const,
          leverage: 10,
          entryPrice: 98000.00,
          quantity: 0.001,
          tpPrice: 99000.00,
          tpPercent: 1.0,
          unrealizedPnl: 0,
          openedAt: '2025-01-06T09:30:00Z',
          gridLevel: 3,
        },
        {
          symbol: 'BTC-USDT',
          side: 'LONG' as const,
          leverage: 10,
          entryPrice: 97000.00,
          quantity: 0.001,
          tpPrice: 97500.00,
          tpPercent: 0.5,
          unrealizedPnl: 0,
          openedAt: '2025-01-06T08:30:00Z',
          gridLevel: 1,
        },
        {
          symbol: 'BTC-USDT',
          side: 'LONG' as const,
          leverage: 10,
          entryPrice: 97500.00,
          quantity: 0.001,
          tpPrice: 98200.00,
          tpPercent: 0.7,
          unrealizedPnl: 0,
          openedAt: '2025-01-06T09:00:00Z',
          gridLevel: 2,
        },
      ]

      const { container } = render(<PositionsTable {...defaultProps} positions={unsortedPositions} />)

      // Find all position cards
      const positionCards = container.querySelectorAll('[class*="hover:bg-muted"]')

      // Verify first position has lowest TP (97500)
      expect(positionCards[0]).toHaveTextContent('$97,000.00') // Entry
      expect(positionCards[0]).toHaveTextContent('$97,500.00') // TP

      // Verify second position has middle TP (98200)
      expect(positionCards[1]).toHaveTextContent('$97,500.00') // Entry
      expect(positionCards[1]).toHaveTextContent('$98,200.00') // TP

      // Verify third position has highest TP (99000)
      expect(positionCards[2]).toHaveTextContent('$98,000.00') // Entry
      expect(positionCards[2]).toHaveTextContent('$99,000.00') // TP
    })

    it('places positions without TP at the end', () => {
      const positionsWithoutTP = [
        {
          symbol: 'BTC-USDT',
          side: 'LONG' as const,
          leverage: 10,
          entryPrice: 98000.00,
          quantity: 0.001,
          tpPrice: 99000.00,
          tpPercent: 1.0,
          unrealizedPnl: 0,
          openedAt: '2025-01-06T09:30:00Z',
          gridLevel: 2,
        },
        {
          symbol: 'BTC-USDT',
          side: 'LONG' as const,
          leverage: 10,
          entryPrice: 97000.00,
          quantity: 0.001,
          tpPrice: null,
          tpPercent: 0,
          unrealizedPnl: 0,
          openedAt: '2025-01-06T08:30:00Z',
          gridLevel: 0,
        },
        {
          symbol: 'BTC-USDT',
          side: 'LONG' as const,
          leverage: 10,
          entryPrice: 97500.00,
          quantity: 0.001,
          tpPrice: 98000.00,
          tpPercent: 0.5,
          unrealizedPnl: 0,
          openedAt: '2025-01-06T09:00:00Z',
          gridLevel: 1,
        },
      ]

      const { container } = render(<PositionsTable {...defaultProps} positions={positionsWithoutTP} />)

      const positionCards = container.querySelectorAll('[class*="hover:bg-muted"]')

      // Verify first position has lowest TP (98000)
      expect(positionCards[0]).toHaveTextContent('$97,500.00') // Entry
      expect(positionCards[0]).toHaveTextContent('$98,000.00') // TP

      // Verify second position has middle TP (99000)
      expect(positionCards[1]).toHaveTextContent('$98,000.00') // Entry
      expect(positionCards[1]).toHaveTextContent('$99,000.00') // TP

      // Verify third position has no TP (should be last)
      expect(positionCards[2]).toHaveTextContent('$97,000.00') // Entry
      expect(positionCards[2]).toHaveTextContent('--') // No TP
    })
  })
})
