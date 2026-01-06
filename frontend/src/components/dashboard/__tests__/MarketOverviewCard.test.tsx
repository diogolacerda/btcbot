/**
 * MarketOverviewCard Component Tests
 *
 * Tests for the market data display including price, funding, MACD, and grid info.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { MarketOverviewCard } from '../MarketOverviewCard'
import {
  mockPrice,
  mockPriceNegative,
  mockFundingRate,
  mockMacdData,
  mockMacdDataBearish,
  mockGridRange,
} from '@/test/mocks'

describe('MarketOverviewCard', () => {
  const defaultProps = {
    price: mockPrice,
    funding: mockFundingRate,
    macd: mockMacdData,
    gridRange: mockGridRange,
    isLoading: false,
    isError: false,
  }

  describe('loading state', () => {
    it('renders loading skeleton when loading', () => {
      const { container } = render(<MarketOverviewCard {...defaultProps} isLoading={true} />)

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
      expect(screen.queryByText('Market Overview')).not.toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('renders error message when error', () => {
      render(<MarketOverviewCard {...defaultProps} isError={true} />)

      expect(screen.getByText('Failed to load market data')).toBeInTheDocument()
    })
  })

  describe('price display', () => {
    it('renders current price', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('$98,500.25')).toBeInTheDocument()
    })

    it('renders positive price change with plus sign', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('+1.28%')).toBeInTheDocument()
    })

    it('renders negative price change', () => {
      render(<MarketOverviewCard {...defaultProps} price={mockPriceNegative} />)

      expect(screen.getByText('-1.52%')).toBeInTheDocument()
    })

    it('renders 24h range', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText(/24h Range:/)).toBeInTheDocument()
      expect(screen.getByText(/\$97,000\.00 - \$99,000\.00/)).toBeInTheDocument()
    })

    it('renders placeholder when price is undefined', () => {
      render(<MarketOverviewCard {...defaultProps} price={undefined} />)

      const placeholders = screen.getAllByText('--')
      expect(placeholders.length).toBeGreaterThan(0)
    })
  })

  describe('funding rate', () => {
    it('renders funding rate section', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('Funding Rate')).toBeInTheDocument()
      expect(screen.getByText('+0.01%')).toBeInTheDocument()
    })

    it('renders next funding time', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText(/Next:/)).toBeInTheDocument()
    })
  })

  describe('MACD signal', () => {
    it('renders bullish signal', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('MACD Signal')).toBeInTheDocument()
      expect(screen.getByText('Bullish')).toBeInTheDocument()
    })

    it('renders bearish signal', () => {
      render(<MarketOverviewCard {...defaultProps} macd={mockMacdDataBearish} />)

      expect(screen.getByText('Bearish')).toBeInTheDocument()
    })

    it('renders histogram direction - rising', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('Histogram: ↑ Rising')).toBeInTheDocument()
    })

    it('renders histogram direction - falling', () => {
      render(<MarketOverviewCard {...defaultProps} macd={mockMacdDataBearish} />)

      expect(screen.getByText('Histogram: ↓ Falling')).toBeInTheDocument()
    })
  })

  describe('MACD values', () => {
    it('renders MACD line and signal values', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('MACD Line / Signal')).toBeInTheDocument()
      expect(screen.getByText('125.50')).toBeInTheDocument()
      expect(screen.getByText('80.30')).toBeInTheDocument()
    })

    it('renders negative MACD values in red', () => {
      render(<MarketOverviewCard {...defaultProps} macd={mockMacdDataBearish} />)

      const macdLine = screen.getByText('-150.00')
      expect(macdLine).toHaveClass('text-red-500')
    })
  })

  describe('grid position', () => {
    it('renders grid position percentage', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('Grid Position')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('renders grid range', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('$97,000.00 - $100,000.00')).toBeInTheDocument()
    })
  })

  describe('volume', () => {
    it('renders 24h volume in millions', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      expect(screen.getByText('24h Volume')).toBeInTheDocument()
      expect(screen.getByText('$15000.00M')).toBeInTheDocument()
    })

    it('does not render volume when price is undefined', () => {
      render(<MarketOverviewCard {...defaultProps} price={undefined} />)

      expect(screen.queryByText('24h Volume')).not.toBeInTheDocument()
    })
  })

  describe('color coding', () => {
    it('applies green color for positive price change', () => {
      render(<MarketOverviewCard {...defaultProps} />)

      const changeElement = screen.getByText('+1.28%')
      expect(changeElement).toHaveClass('text-green-500')
    })

    it('applies red color for negative price change', () => {
      render(<MarketOverviewCard {...defaultProps} price={mockPriceNegative} />)

      const changeElement = screen.getByText('-1.52%')
      expect(changeElement).toHaveClass('text-red-500')
    })
  })
})
