/**
 * Tests for useEngagement hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as api from '@/lib/api'
import {
  useEngagements,
  useEngagement,
  useCreateEngagement,
  useUpdateEngagementStatus,
} from '@/lib/hooks/use-engagement'

// Mock the API module
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual('@/lib/api')
  return {
    ...actual,
    getEngagements: vi.fn(),
    getEngagement: vi.fn(),
    createEngagement: vi.fn(),
    updateEngagementStatus: vi.fn(),
  }
})

const mockEngagements = {
  items: [
    {
      id: 'eng-1',
      name: 'Engagement 1',
      status: 'in_progress',
      priority: 'high',
      created_by: 'user@example.com',
      created_at: '2026-01-15T10:00:00Z',
      updated_at: '2026-01-19T08:30:00Z',
    },
    {
      id: 'eng-2',
      name: 'Engagement 2',
      status: 'draft',
      priority: 'low',
      created_by: 'user@example.com',
      created_at: '2026-01-10T10:00:00Z',
      updated_at: '2026-01-18T08:30:00Z',
    },
  ],
  total: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
}

const mockEngagement = {
  id: 'eng-1',
  name: 'Engagement 1',
  description: 'Test engagement',
  objective: 'Test objective',
  status: 'in_progress',
  priority: 'high',
  data_sources: [],
  tags: ['test'],
  requires_approval: true,
  created_by: 'user@example.com',
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-19T08:30:00Z',
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useEngagements', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches engagements successfully', async () => {
    vi.mocked(api.getEngagements).mockResolvedValue(mockEngagements)

    const { result } = renderHook(() => useEngagements(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockEngagements)
    expect(api.getEngagements).toHaveBeenCalled()
  })

  it('passes filter parameters to API', async () => {
    vi.mocked(api.getEngagements).mockResolvedValue(mockEngagements)

    renderHook(
      () => useEngagements({ status: 'in_progress', priority: 'high' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(api.getEngagements).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'in_progress',
          priority: 'high',
        })
      )
    })
  })

  it('handles pagination parameters', async () => {
    vi.mocked(api.getEngagements).mockResolvedValue(mockEngagements)

    renderHook(
      () => useEngagements({ page: 2, page_size: 20 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(api.getEngagements).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
          page_size: 20,
        })
      )
    })
  })

  it('handles API errors', async () => {
    const error = new Error('API Error')
    vi.mocked(api.getEngagements).mockRejectedValue(error)

    const { result } = renderHook(() => useEngagements(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe('useEngagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches single engagement by id', async () => {
    vi.mocked(api.getEngagement).mockResolvedValue(mockEngagement)

    const { result } = renderHook(() => useEngagement('eng-1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockEngagement)
    expect(api.getEngagement).toHaveBeenCalledWith('eng-1')
  })

  it('does not fetch when id is undefined', () => {
    const { result } = renderHook(() => useEngagement(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
    expect(api.getEngagement).not.toHaveBeenCalled()
  })

  it('handles not found errors', async () => {
    const error = new Error('Engagement not found')
    vi.mocked(api.getEngagement).mockRejectedValue(error)

    const { result } = renderHook(() => useEngagement('invalid-id'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe('useCreateEngagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates engagement successfully', async () => {
    vi.mocked(api.createEngagement).mockResolvedValue(mockEngagement)

    const { result } = renderHook(() => useCreateEngagement(), {
      wrapper: createWrapper(),
    })

    const newEngagement = {
      name: 'New Engagement',
      objective: 'Test objective',
    }

    result.current.mutate(newEngagement)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(api.createEngagement).toHaveBeenCalledWith(newEngagement)
    expect(result.current.data).toEqual(mockEngagement)
  })

  it('handles creation errors', async () => {
    const error = new Error('Validation error')
    vi.mocked(api.createEngagement).mockRejectedValue(error)

    const { result } = renderHook(() => useCreateEngagement(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ name: '', objective: '' })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe('useUpdateEngagementStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('updates engagement status', async () => {
    const updatedEngagement = { ...mockEngagement, status: 'completed' as const }
    vi.mocked(api.updateEngagementStatus).mockResolvedValue(updatedEngagement)

    const { result } = renderHook(() => useUpdateEngagementStatus(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      id: 'eng-1',
      status: 'completed',
      reason: 'Task completed',
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(api.updateEngagementStatus).toHaveBeenCalledWith(
      'eng-1',
      'completed',
      'Task completed'
    )
  })

  it('handles status update errors', async () => {
    const error = new Error('Cannot update status')
    vi.mocked(api.updateEngagementStatus).mockRejectedValue(error)

    const { result } = renderHook(() => useUpdateEngagementStatus(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      id: 'eng-1',
      status: 'completed',
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})
