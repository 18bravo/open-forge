/**
 * Tests for EngagementCard component
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EngagementCard, EngagementCardSkeleton } from '@/components/engagements/EngagementCard'
import type { EngagementSummary } from '@/lib/api'

const mockEngagement: EngagementSummary = {
  id: 'eng-123',
  name: 'Test Engagement',
  status: 'in_progress',
  priority: 'high',
  created_by: 'john.doe@example.com',
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-19T08:30:00Z',
}

describe('EngagementCard', () => {
  describe('rendering', () => {
    it('renders engagement name', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      expect(screen.getByText('Test Engagement')).toBeInTheDocument()
    })

    it('renders creator name', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      expect(screen.getByText('john.doe@example.com')).toBeInTheDocument()
    })

    it('renders status badge', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      expect(screen.getByText('In Progress')).toBeInTheDocument()
    })

    it('renders priority indicator', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      expect(screen.getByText('high')).toBeInTheDocument()
    })

    it('renders as a link to engagement detail', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      const link = screen.getByRole('link')
      expect(link).toHaveAttribute('href', '/engagements/eng-123')
    })
  })

  describe('priority indicators', () => {
    it('displays low priority correctly', () => {
      const engagement = { ...mockEngagement, priority: 'low' as const }
      render(<EngagementCard engagement={engagement} />)
      const priorityText = screen.getByText('low')
      expect(priorityText.closest('div')).toHaveClass('text-slate-500')
    })

    it('displays medium priority correctly', () => {
      const engagement = { ...mockEngagement, priority: 'medium' as const }
      render(<EngagementCard engagement={engagement} />)
      const priorityText = screen.getByText('medium')
      expect(priorityText.closest('div')).toHaveClass('text-blue-500')
    })

    it('displays high priority correctly', () => {
      const engagement = { ...mockEngagement, priority: 'high' as const }
      render(<EngagementCard engagement={engagement} />)
      const priorityText = screen.getByText('high')
      expect(priorityText.closest('div')).toHaveClass('text-orange-500')
    })

    it('displays critical priority correctly', () => {
      const engagement = { ...mockEngagement, priority: 'critical' as const }
      render(<EngagementCard engagement={engagement} />)
      const priorityText = screen.getByText('critical')
      expect(priorityText.closest('div')).toHaveClass('text-red-500')
    })
  })

  describe('status variations', () => {
    it('shows Draft status', () => {
      const engagement = { ...mockEngagement, status: 'draft' as const }
      render(<EngagementCard engagement={engagement} />)
      expect(screen.getByText('Draft')).toBeInTheDocument()
    })

    it('shows Completed status', () => {
      const engagement = { ...mockEngagement, status: 'completed' as const }
      render(<EngagementCard engagement={engagement} />)
      expect(screen.getByText('Completed')).toBeInTheDocument()
    })

    it('shows Failed status', () => {
      const engagement = { ...mockEngagement, status: 'failed' as const }
      render(<EngagementCard engagement={engagement} />)
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })

    it('shows Paused status', () => {
      const engagement = { ...mockEngagement, status: 'paused' as const }
      render(<EngagementCard engagement={engagement} />)
      expect(screen.getByText('Paused')).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('applies custom className', () => {
      render(<EngagementCard engagement={mockEngagement} className="custom-class" />)
      // The Card component should have the custom class
      const card = screen.getByRole('link').firstChild
      expect(card).toHaveClass('custom-class')
    })

    it('applies hover styles', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      const card = screen.getByRole('link').firstChild
      expect(card).toHaveClass('hover:shadow-md')
      expect(card).toHaveClass('hover:border-primary/50')
    })

    it('applies group class for arrow animation', () => {
      render(<EngagementCard engagement={mockEngagement} />)
      const card = screen.getByRole('link').firstChild
      expect(card).toHaveClass('group')
    })
  })

  describe('time display', () => {
    it('displays relative time from updated_at', () => {
      // Note: The actual text depends on formatRelativeTime implementation
      // and the current time
      render(<EngagementCard engagement={mockEngagement} />)
      // Should show some time indicator
      const timeIndicator = screen.getByText(/ago|just now/i)
      expect(timeIndicator).toBeInTheDocument()
    })
  })
})

describe('EngagementCardSkeleton', () => {
  it('renders skeleton card', () => {
    render(<EngagementCardSkeleton />)
    // Skeleton should have animate-pulse class
    const skeleton = document.querySelector('.animate-pulse')
    expect(skeleton).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<EngagementCardSkeleton className="custom-skeleton" />)
    const skeleton = document.querySelector('.custom-skeleton')
    expect(skeleton).toBeInTheDocument()
  })

  it('renders placeholder elements for content', () => {
    render(<EngagementCardSkeleton />)
    // Should have multiple bg-muted placeholder elements
    const placeholders = document.querySelectorAll('.bg-muted')
    expect(placeholders.length).toBeGreaterThan(0)
  })
})
