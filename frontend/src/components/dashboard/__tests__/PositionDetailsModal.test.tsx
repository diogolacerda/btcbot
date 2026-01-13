/**
 * PositionDetailsModal Component Tests
 *
 * Tests for the position details modal dialog.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { PositionDetailsModal } from '../PositionDetailsModal'
import { mockPositions } from '@/test/mocks'

describe('PositionDetailsModal', () => {
  const defaultProps = {
    position: mockPositions[0],
    currentPrice: 98000.00,
    isOpen: true,
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders nothing when closed', () => {
      render(<PositionDetailsModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('renders nothing when position is null', () => {
      render(<PositionDetailsModal {...defaultProps} position={null} />)

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('renders dialog when open with position', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('renders title and symbol', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Position Details')).toBeInTheDocument()
      expect(screen.getByText(/BTC-USDT/)).toBeInTheDocument()
    })
  })

  describe('position info', () => {
    it('renders side with correct color', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      const sideElement = screen.getByText('LONG')
      expect(sideElement).toHaveClass('text-green-500')
    })

    it('renders quantity', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('0.0010 BTC')).toBeInTheDocument()
    })

    it('renders leverage', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Leverage:')).toBeInTheDocument()
      expect(screen.getByText('10x')).toBeInTheDocument()
    })
  })

  describe('P&L display', () => {
    it('shows unrealized P&L', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Unrealized P&L')).toBeInTheDocument()
    })

    it('calculates positive P&L correctly', () => {
      // Entry: 97500, Current: 98000, Qty: 0.001
      // PnL = (98000 - 97500) * 0.001 = 0.50
      render(<PositionDetailsModal {...defaultProps} />)

      // P&L appears multiple times (unrealized and expected profit)
      const pnlElements = screen.getAllByText('+$0.50')
      expect(pnlElements.length).toBeGreaterThan(0)
    })

    it('renders P&L in green when profitable', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      // Find the unrealized P&L specifically (inside the bg-muted/50 section)
      const pnlElements = screen.getAllByText('+$0.50')
      expect(pnlElements[0]).toHaveClass('text-green-500')
    })

    it('renders P&L in red when losing', () => {
      render(<PositionDetailsModal {...defaultProps} currentPrice={97000.00} />)

      const pnlElements = screen.getAllByText(/\$0\.50/)
      // Find the one with red class
      const redPnl = pnlElements.find(el => el.classList.contains('text-red-500'))
      expect(redPnl).toBeTruthy()
    })
  })

  describe('price information', () => {
    it('renders entry price', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Entry Price')).toBeInTheDocument()
      expect(screen.getByText('$97,500.00')).toBeInTheDocument()
    })

    it('renders TP price', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('TP Price')).toBeInTheDocument()
      // TP price ($98,000) and current price ($98,000) are the same, so multiple elements
      const priceElements = screen.getAllByText('$98,000.00')
      expect(priceElements.length).toBeGreaterThan(0)
    })

    it('renders current price when available', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Current Price')).toBeInTheDocument()
    })

    it('renders distance to TP', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Distance to TP')).toBeInTheDocument()
    })
  })

  describe('position value', () => {
    it('renders entry value', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Entry Value')).toBeInTheDocument()
    })

    it('renders TP value', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('TP Value')).toBeInTheDocument()
    })

    it('renders expected profit', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Expected Profit')).toBeInTheDocument()
    })
  })

  describe('timeline', () => {
    it('renders opened timestamp', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      expect(screen.getByText('Opened At')).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<PositionDetailsModal {...defaultProps} onClose={onClose} />)

      // Click the X button
      await user.click(screen.getByText('×'))

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when footer Close button is clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<PositionDetailsModal {...defaultProps} onClose={onClose} />)

      await user.click(screen.getByRole('button', { name: 'Close' }))

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when backdrop is clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      const { container } = render(<PositionDetailsModal {...defaultProps} onClose={onClose} />)

      const backdrop = container.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
      }

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when Escape key is pressed', () => {
      const onClose = vi.fn()
      render(<PositionDetailsModal {...defaultProps} onClose={onClose} />)

      fireEvent.keyDown(document, { key: 'Escape' })

      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('accessibility', () => {
    it('has correct aria attributes', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby', 'position-modal-title')
    })

    it('dialog is focusable', () => {
      render(<PositionDetailsModal {...defaultProps} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('tabIndex', '-1')
    })
  })
})
