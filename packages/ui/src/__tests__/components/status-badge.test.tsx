/**
 * Tests for StatusBadge component
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '@/components/engagements/StatusBadge'

describe('StatusBadge', () => {
  describe('engagement statuses', () => {
    it('renders draft status', () => {
      render(<StatusBadge status="draft" />)
      expect(screen.getByText('Draft')).toBeInTheDocument()
    })

    it('renders pending_approval status', () => {
      render(<StatusBadge status="pending_approval" />)
      expect(screen.getByText('Pending Approval')).toBeInTheDocument()
    })

    it('renders approved status', () => {
      render(<StatusBadge status="approved" />)
      expect(screen.getByText('Approved')).toBeInTheDocument()
    })

    it('renders in_progress status', () => {
      render(<StatusBadge status="in_progress" />)
      expect(screen.getByText('In Progress')).toBeInTheDocument()
    })

    it('renders paused status', () => {
      render(<StatusBadge status="paused" />)
      expect(screen.getByText('Paused')).toBeInTheDocument()
    })

    it('renders completed status', () => {
      render(<StatusBadge status="completed" />)
      expect(screen.getByText('Completed')).toBeInTheDocument()
    })

    it('renders cancelled status', () => {
      render(<StatusBadge status="cancelled" />)
      expect(screen.getByText('Cancelled')).toBeInTheDocument()
    })

    it('renders failed status', () => {
      render(<StatusBadge status="failed" />)
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })
  })

  describe('approval statuses', () => {
    it('renders pending status', () => {
      render(<StatusBadge status="pending" />)
      expect(screen.getByText('Pending')).toBeInTheDocument()
    })

    it('renders rejected status', () => {
      render(<StatusBadge status="rejected" />)
      expect(screen.getByText('Rejected')).toBeInTheDocument()
    })

    it('renders expired status', () => {
      render(<StatusBadge status="expired" />)
      expect(screen.getByText('Expired')).toBeInTheDocument()
    })
  })

  describe('agent task statuses', () => {
    it('renders queued status', () => {
      render(<StatusBadge status="queued" />)
      expect(screen.getByText('Queued')).toBeInTheDocument()
    })

    it('renders running status', () => {
      render(<StatusBadge status="running" />)
      expect(screen.getByText('Running')).toBeInTheDocument()
    })

    it('renders waiting_approval status', () => {
      render(<StatusBadge status="waiting_approval" />)
      expect(screen.getByText('Waiting Approval')).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('applies correct classes for completed status', () => {
      render(<StatusBadge status="completed" />)
      const badge = screen.getByText('Completed')
      expect(badge).toHaveClass('bg-green-100')
      expect(badge).toHaveClass('text-green-700')
    })

    it('applies correct classes for failed status', () => {
      render(<StatusBadge status="failed" />)
      const badge = screen.getByText('Failed')
      expect(badge).toHaveClass('bg-red-100')
      expect(badge).toHaveClass('text-red-700')
    })

    it('applies correct classes for in_progress status', () => {
      render(<StatusBadge status="in_progress" />)
      const badge = screen.getByText('In Progress')
      expect(badge).toHaveClass('bg-cyan-100')
      expect(badge).toHaveClass('text-cyan-700')
    })

    it('applies rounded-full class', () => {
      render(<StatusBadge status="draft" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('rounded-full')
    })

    it('applies font-medium class', () => {
      render(<StatusBadge status="draft" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('font-medium')
    })
  })

  describe('sizes', () => {
    it('applies small size classes', () => {
      render(<StatusBadge status="draft" size="sm" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs')
    })

    it('applies default size classes', () => {
      render(<StatusBadge status="draft" size="default" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('px-2.5', 'py-1', 'text-xs')
    })

    it('applies large size classes', () => {
      render(<StatusBadge status="draft" size="lg" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('px-3', 'py-1.5', 'text-sm')
    })

    it('uses default size when not specified', () => {
      render(<StatusBadge status="draft" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('px-2.5', 'py-1')
    })
  })

  describe('custom className', () => {
    it('merges custom className with default classes', () => {
      render(<StatusBadge status="draft" className="custom-class" />)
      const badge = screen.getByText('Draft')
      expect(badge).toHaveClass('custom-class')
      expect(badge).toHaveClass('rounded-full')
    })
  })

  describe('unknown status', () => {
    it('renders unknown status as raw value', () => {
      // @ts-expect-error Testing unknown status
      render(<StatusBadge status="unknown_status" />)
      expect(screen.getByText('unknown_status')).toBeInTheDocument()
    })

    it('applies fallback styling for unknown status', () => {
      // @ts-expect-error Testing unknown status
      render(<StatusBadge status="unknown_status" />)
      const badge = screen.getByText('unknown_status')
      expect(badge).toHaveClass('bg-gray-100')
      expect(badge).toHaveClass('text-gray-700')
    })
  })
})
