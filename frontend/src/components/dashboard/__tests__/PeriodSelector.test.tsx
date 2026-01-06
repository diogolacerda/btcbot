/**
 * PeriodSelector Component Tests
 *
 * Tests for the period selection component that allows users
 * to filter dashboard data by time periods.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { PeriodSelector } from '../PeriodSelector'

describe('PeriodSelector', () => {
  const defaultProps = {
    value: 'today' as const,
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders all period options', () => {
      render(<PeriodSelector {...defaultProps} />)

      expect(screen.getByRole('button', { name: 'Today' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '7 Days' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '30 Days' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Custom' })).toBeInTheDocument()
    })

    it('highlights the selected period', () => {
      render(<PeriodSelector {...defaultProps} value="7days" />)

      const button7days = screen.getByRole('button', { name: '7 Days' })
      expect(button7days).toHaveClass('bg-primary')
    })

    it('does not show date picker by default', () => {
      render(<PeriodSelector {...defaultProps} />)

      expect(screen.queryByLabelText(/start date/i)).not.toBeInTheDocument()
      expect(screen.queryByLabelText(/end date/i)).not.toBeInTheDocument()
    })
  })

  describe('period selection', () => {
    it('calls onChange when selecting a non-custom period', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<PeriodSelector {...defaultProps} onChange={onChange} />)

      await user.click(screen.getByRole('button', { name: '7 Days' }))

      expect(onChange).toHaveBeenCalledWith('7days')
    })

    it('calls onChange when selecting 30 days', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<PeriodSelector {...defaultProps} onChange={onChange} />)

      await user.click(screen.getByRole('button', { name: '30 Days' }))

      expect(onChange).toHaveBeenCalledWith('30days')
    })

    it('shows date picker when selecting Custom', async () => {
      const user = userEvent.setup()
      const { container } = render(<PeriodSelector {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Custom' }))

      // Should show date inputs and Apply button
      const dateInputs = container.querySelectorAll('input[type="date"]')
      expect(dateInputs).toHaveLength(2)
      expect(screen.getByRole('button', { name: 'Apply' })).toBeInTheDocument()
    })
  })

  describe('custom date range', () => {
    it('Apply button is disabled when dates are empty', async () => {
      const user = userEvent.setup()
      render(<PeriodSelector {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Custom' }))

      const applyButton = screen.getByRole('button', { name: 'Apply' })
      expect(applyButton).toBeDisabled()
    })

    it('calls onChange with dates when Apply is clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      const { container } = render(<PeriodSelector {...defaultProps} onChange={onChange} />)

      await user.click(screen.getByRole('button', { name: 'Custom' }))

      const dateInputs = container.querySelectorAll('input[type="date"]')
      const startInput = dateInputs[0] as HTMLInputElement
      const endInput = dateInputs[1] as HTMLInputElement

      // For date inputs, we need to set value directly and fire change event
      await user.clear(startInput)
      await user.type(startInput, '2025-01-01')
      await user.clear(endInput)
      await user.type(endInput, '2025-01-06')

      await user.click(screen.getByRole('button', { name: 'Apply' }))

      expect(onChange).toHaveBeenCalledWith('custom', '2025-01-01', '2025-01-06')
    })

    it('hides date picker after Apply is clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(<PeriodSelector {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Custom' }))

      const dateInputs = container.querySelectorAll('input[type="date"]')
      const startInput = dateInputs[0] as HTMLInputElement
      const endInput = dateInputs[1] as HTMLInputElement

      await user.clear(startInput)
      await user.type(startInput, '2025-01-01')
      await user.clear(endInput)
      await user.type(endInput, '2025-01-06')

      await user.click(screen.getByRole('button', { name: 'Apply' }))

      expect(screen.queryByRole('button', { name: 'Apply' })).not.toBeInTheDocument()
    })

    it('hides date picker when switching to non-custom period', async () => {
      const user = userEvent.setup()
      render(<PeriodSelector {...defaultProps} />)

      // Open custom picker
      await user.click(screen.getByRole('button', { name: 'Custom' }))
      expect(screen.getByRole('button', { name: 'Apply' })).toBeInTheDocument()

      // Switch to 7 days
      await user.click(screen.getByRole('button', { name: '7 Days' }))
      expect(screen.queryByRole('button', { name: 'Apply' })).not.toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <PeriodSelector {...defaultProps} className="custom-class" />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })
})
