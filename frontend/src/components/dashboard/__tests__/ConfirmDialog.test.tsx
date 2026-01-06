/**
 * ConfirmDialog Component Tests
 *
 * Tests for the confirmation modal used for dangerous actions.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { ConfirmDialog } from '../ConfirmDialog'

describe('ConfirmDialog', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders nothing when closed', () => {
      render(<ConfirmDialog {...defaultProps} isOpen={false} />)

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('renders dialog when open', () => {
      render(<ConfirmDialog {...defaultProps} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('renders title and message', () => {
      render(<ConfirmDialog {...defaultProps} />)

      expect(screen.getByText('Confirm Action')).toBeInTheDocument()
      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument()
    })

    it('renders default button labels', () => {
      render(<ConfirmDialog {...defaultProps} />)

      expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    })

    it('renders custom button labels', () => {
      render(
        <ConfirmDialog
          {...defaultProps}
          confirmLabel="Yes, Delete"
          cancelLabel="No, Keep"
        />
      )

      expect(screen.getByRole('button', { name: 'Yes, Delete' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'No, Keep' })).toBeInTheDocument()
    })
  })

  describe('variants', () => {
    it('applies default variant styling', () => {
      render(<ConfirmDialog {...defaultProps} />)

      const confirmButton = screen.getByRole('button', { name: 'Confirm' })
      expect(confirmButton).toHaveClass('bg-primary')
    })

    it('applies danger variant styling', () => {
      render(<ConfirmDialog {...defaultProps} variant="danger" />)

      const confirmButton = screen.getByRole('button', { name: 'Confirm' })
      expect(confirmButton).toHaveClass('bg-destructive')
    })
  })

  describe('interactions', () => {
    it('calls onConfirm when confirm button is clicked', async () => {
      const user = userEvent.setup()
      const onConfirm = vi.fn()
      render(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />)

      await user.click(screen.getByRole('button', { name: 'Confirm' }))

      expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    it('calls onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup()
      const onCancel = vi.fn()
      render(<ConfirmDialog {...defaultProps} onCancel={onCancel} />)

      await user.click(screen.getByRole('button', { name: 'Cancel' }))

      expect(onCancel).toHaveBeenCalledTimes(1)
    })

    it('calls onCancel when backdrop is clicked', async () => {
      const user = userEvent.setup()
      const onCancel = vi.fn()
      const { container } = render(<ConfirmDialog {...defaultProps} onCancel={onCancel} />)

      // Click the backdrop (first child with bg-black class)
      const backdrop = container.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
      }

      expect(onCancel).toHaveBeenCalledTimes(1)
    })

    it('calls onCancel when Escape key is pressed', async () => {
      const onCancel = vi.fn()
      render(<ConfirmDialog {...defaultProps} onCancel={onCancel} />)

      fireEvent.keyDown(document, { key: 'Escape' })

      expect(onCancel).toHaveBeenCalledTimes(1)
    })

    it('does not call onCancel on Escape when closed', () => {
      const onCancel = vi.fn()
      render(<ConfirmDialog {...defaultProps} isOpen={false} onCancel={onCancel} />)

      fireEvent.keyDown(document, { key: 'Escape' })

      expect(onCancel).not.toHaveBeenCalled()
    })
  })

  describe('accessibility', () => {
    it('has correct aria attributes', () => {
      render(<ConfirmDialog {...defaultProps} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby', 'dialog-title')
    })

    it('title has correct id for aria-labelledby', () => {
      render(<ConfirmDialog {...defaultProps} />)

      const title = screen.getByText('Confirm Action')
      expect(title).toHaveAttribute('id', 'dialog-title')
    })

    it('dialog is focusable', () => {
      render(<ConfirmDialog {...defaultProps} />)

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('tabIndex', '-1')
    })
  })
})
