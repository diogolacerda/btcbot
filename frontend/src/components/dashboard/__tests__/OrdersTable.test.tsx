/**
 * OrdersTable Component Tests
 *
 * Tests for the orders table displaying pending and filled orders.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { OrdersTable } from '../OrdersTable'
import { mockOrders } from '@/test/mocks'
import type { OrdersListResponse } from '@/types/api'

describe('OrdersTable', () => {
  const defaultData: OrdersListResponse = {
    orders: mockOrders,
    total: mockOrders.length,
    limit: 10,
    offset: 0,
    pendingCount: 1,
    filledCount: 1,
  }

  const defaultProps = {
    data: defaultData,
    isLoading: false,
    isError: false,
  }

  describe('loading state', () => {
    it('renders loading skeleton when loading', () => {
      const { container } = render(<OrdersTable {...defaultProps} isLoading={true} />)

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders error message when error', () => {
      render(<OrdersTable {...defaultProps} isError={true} />)

      expect(screen.getByText('Failed to load orders')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('renders empty message when no orders', () => {
      const emptyData: OrdersListResponse = {
        ...defaultData,
        orders: [],
        total: 0,
        pendingCount: 0,
        filledCount: 0,
      }
      render(<OrdersTable {...defaultProps} data={emptyData} />)

      expect(screen.getByText('No active orders')).toBeInTheDocument()
      expect(screen.getByText('Orders will appear when the bot is trading')).toBeInTheDocument()
    })
  })

  describe('header', () => {
    it('renders title', () => {
      render(<OrdersTable {...defaultProps} />)

      expect(screen.getByText('Orders')).toBeInTheDocument()
    })

    it('renders pending and filled counts', () => {
      render(<OrdersTable {...defaultProps} />)

      expect(screen.getByText(/Pending:/)).toBeInTheDocument()
      expect(screen.getByText(/Filled:/)).toBeInTheDocument()
      // Both counts are 1, check they exist with correct styles
      const pendingCount = screen.getByText('1', { selector: '.text-yellow-500' })
      const filledCount = screen.getByText('1', { selector: '.text-blue-500' })
      expect(pendingCount).toBeInTheDocument()
      expect(filledCount).toBeInTheDocument()
    })
  })

  describe('table headers', () => {
    it('renders all column headers', () => {
      render(<OrdersTable {...defaultProps} />)

      expect(screen.getByText('Side')).toBeInTheDocument()
      expect(screen.getByText('Price')).toBeInTheDocument()
      expect(screen.getByText('TP Price')).toBeInTheDocument()
      expect(screen.getByText('Qty')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Created')).toBeInTheDocument()
    })
  })

  describe('order data', () => {
    it('renders order side with correct color', () => {
      render(<OrdersTable {...defaultProps} />)

      const longElements = screen.getAllByText('LONG')
      expect(longElements[0]).toHaveClass('text-green-500')
    })

    it('renders order prices', () => {
      render(<OrdersTable {...defaultProps} />)

      // $98,000 appears multiple times (as entry and TP prices)
      const priceElements = screen.getAllByText('$98,000.00')
      expect(priceElements.length).toBeGreaterThan(0)
      expect(screen.getByText('$98,500.00')).toBeInTheDocument()
    })

    it('renders order quantity', () => {
      render(<OrdersTable {...defaultProps} />)

      const qtyElements = screen.getAllByText('0.0010')
      expect(qtyElements.length).toBeGreaterThan(0)
    })
  })

  describe('status badges', () => {
    it('renders Pending status badge', () => {
      render(<OrdersTable {...defaultProps} />)

      const pendingBadge = screen.getByText('Pending')
      expect(pendingBadge).toHaveClass('text-yellow-500')
    })

    it('renders Filled status badge', () => {
      render(<OrdersTable {...defaultProps} />)

      const filledBadge = screen.getByText('Filled')
      expect(filledBadge).toHaveClass('text-blue-500')
    })

    it('renders TP Hit status badge', () => {
      render(<OrdersTable {...defaultProps} />)

      const tpHitBadge = screen.getByText('TP Hit')
      expect(tpHitBadge).toHaveClass('text-green-500')
    })
  })

  describe('pagination info', () => {
    it('shows pagination message when there are more orders', () => {
      const dataWithMore: OrdersListResponse = {
        ...defaultData,
        total: 20,
      }
      render(<OrdersTable {...defaultProps} data={dataWithMore} />)

      expect(screen.getByText(/Showing 3 of 20 orders/)).toBeInTheDocument()
    })

    it('does not show pagination when all orders are displayed', () => {
      render(<OrdersTable {...defaultProps} />)

      expect(screen.queryByText(/Showing/)).not.toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onOrderClick when row is clicked', async () => {
      const user = userEvent.setup()
      const onOrderClick = vi.fn()
      render(<OrdersTable {...defaultProps} onOrderClick={onOrderClick} />)

      const rows = screen.getAllByRole('row')
      // First row is header, click the second row (first data row)
      await user.click(rows[1])

      expect(onOrderClick).toHaveBeenCalledWith(mockOrders[0])
    })

    it('applies cursor-pointer class when onOrderClick is provided', () => {
      const onOrderClick = vi.fn()
      render(<OrdersTable {...defaultProps} onOrderClick={onOrderClick} />)

      const rows = screen.getAllByRole('row')
      expect(rows[1]).toHaveClass('cursor-pointer')
    })

    it('does not apply cursor-pointer class when onOrderClick is not provided', () => {
      render(<OrdersTable {...defaultProps} />)

      const rows = screen.getAllByRole('row')
      expect(rows[1]).not.toHaveClass('cursor-pointer')
    })
  })
})
