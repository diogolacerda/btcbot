/**
 * PerformanceMetricsCard Component Tests
 *
 * Tests for trading performance display including P&L, win rate, and trade stats.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { PerformanceMetricsCard } from '../PerformanceMetricsCard'
import { mockPerformanceMetrics } from '@/test/mocks'
import type { PerformanceMetricsResponse } from '@/types/api'

describe('PerformanceMetricsCard', () => {
  const defaultProps = {
    data: mockPerformanceMetrics,
    isLoading: false,
    isError: false,
  }

  describe('loading state', () => {
    it('renders loading skeleton when loading', () => {
      const { container } = render(<PerformanceMetricsCard {...defaultProps} isLoading={true} />)

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders error message when error', () => {
      render(<PerformanceMetricsCard {...defaultProps} isError={true} />)

      expect(screen.getByText('Failed to load performance data')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('renders empty state when data is undefined', () => {
      render(<PerformanceMetricsCard {...defaultProps} data={undefined} />)

      expect(screen.getByText('No trading data available')).toBeInTheDocument()
      expect(screen.getByText('Start trading to see metrics')).toBeInTheDocument()
    })
  })

  describe('data display', () => {
    it('renders title and period', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Performance Metrics')).toBeInTheDocument()
      expect(screen.getByText('7days')).toBeInTheDocument()
    })

    it('renders realized P&L with positive value', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Realized P&L')).toBeInTheDocument()
      expect(screen.getByText('+$850.25')).toBeInTheDocument()
      expect(screen.getByText('(+8.50%)')).toBeInTheDocument()
    })

    it('renders negative P&L with red styling', () => {
      const negativeData: PerformanceMetricsResponse = {
        ...mockPerformanceMetrics,
        periodMetrics: {
          ...mockPerformanceMetrics.periodMetrics,
          realizedPnl: -250.50,
          pnlPercent: -2.5,
        },
      }
      render(<PerformanceMetricsCard {...defaultProps} data={negativeData} />)

      // formatCurrency uses Math.abs so negative values show without minus sign
      const pnlElement = screen.getByText('$250.50')
      expect(pnlElement).toHaveClass('text-red-500')
    })

    it('renders trade count', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Trades')).toBeInTheDocument()
      expect(screen.getByText('45')).toBeInTheDocument()
    })

    it('renders win rate with green color for high rate', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Win Rate')).toBeInTheDocument()
      const winRateElement = screen.getByText('84%')
      expect(winRateElement).toHaveClass('text-green-500')
    })

    it('renders win rate with red color for low rate', () => {
      const lowWinRateData: PerformanceMetricsResponse = {
        ...mockPerformanceMetrics,
        periodMetrics: {
          ...mockPerformanceMetrics.periodMetrics,
          winRate: 35,
        },
      }
      render(<PerformanceMetricsCard {...defaultProps} data={lowWinRateData} />)

      const winRateElement = screen.getByText('35%')
      expect(winRateElement).toHaveClass('text-red-500')
    })

    it('renders win/loss ratio', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('W/L')).toBeInTheDocument()
      expect(screen.getByText('38')).toBeInTheDocument() // Winning trades
      expect(screen.getByText('7')).toBeInTheDocument()  // Losing trades
    })
  })

  describe('total stats', () => {
    it('renders total P&L', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Total P&L (All Time)')).toBeInTheDocument()
      expect(screen.getByText('+$12500.75')).toBeInTheDocument()
    })

    it('renders average profit per trade', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Avg Profit/Trade')).toBeInTheDocument()
      expect(screen.getByText('+$27.78')).toBeInTheDocument()
    })

    it('renders best trade', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Best Trade')).toBeInTheDocument()
      expect(screen.getByText('+$125.50')).toBeInTheDocument()
    })

    it('renders worst trade', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Worst Trade')).toBeInTheDocument()
      // formatCurrency uses Math.abs, negative values shown without sign
      expect(screen.getByText('$35.25')).toBeInTheDocument()
    })

    it('renders total fees', () => {
      render(<PerformanceMetricsCard {...defaultProps} />)

      expect(screen.getByText('Total Fees')).toBeInTheDocument()
      expect(screen.getByText('-$125.50')).toBeInTheDocument()
    })
  })
})
