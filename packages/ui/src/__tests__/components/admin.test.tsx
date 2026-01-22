/**
 * Tests for Admin dashboard components
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SystemHealthCard } from '@/components/admin/SystemHealthCard'
import { AgentStatusGrid } from '@/components/admin/AgentStatusGrid'
import { PipelineStatusTable } from '@/components/admin/PipelineStatusTable'

describe('SystemHealthCard', () => {
  const mockHealthy = {
    service: 'API Gateway',
    status: 'healthy' as const,
    latency: 45,
    uptime: 99.99,
  }

  const mockDegraded = {
    service: 'Redis Cache',
    status: 'degraded' as const,
    latency: 150,
    uptime: 98.5,
  }

  const mockDown = {
    service: 'Worker Service',
    status: 'down' as const,
    latency: 0,
    uptime: 85.0,
  }

  it('renders service name', () => {
    render(<SystemHealthCard health={mockHealthy} />)
    expect(screen.getByText('API Gateway')).toBeInTheDocument()
  })

  it('renders healthy status', () => {
    render(<SystemHealthCard health={mockHealthy} />)
    expect(screen.getByText('healthy')).toBeInTheDocument()
  })

  it('renders degraded status', () => {
    render(<SystemHealthCard health={mockDegraded} />)
    expect(screen.getByText('degraded')).toBeInTheDocument()
  })

  it('renders down status', () => {
    render(<SystemHealthCard health={mockDown} />)
    expect(screen.getByText('down')).toBeInTheDocument()
  })

  it('renders latency value with ms unit', () => {
    render(<SystemHealthCard health={mockHealthy} />)
    expect(screen.getByText('45ms')).toBeInTheDocument()
  })

  it('renders uptime percentage', () => {
    render(<SystemHealthCard health={mockHealthy} />)
    expect(screen.getByText('99.99% uptime')).toBeInTheDocument()
  })

  it('applies green styling for healthy status', () => {
    const { container } = render(<SystemHealthCard health={mockHealthy} />)
    const card = container.firstChild
    expect(card).toHaveClass('border-green-500/30')
    expect(card).toHaveClass('bg-green-500/5')
  })

  it('applies yellow styling for degraded status', () => {
    const { container } = render(<SystemHealthCard health={mockDegraded} />)
    const card = container.firstChild
    expect(card).toHaveClass('border-yellow-500/30')
    expect(card).toHaveClass('bg-yellow-500/5')
  })

  it('applies red styling for down status', () => {
    const { container } = render(<SystemHealthCard health={mockDown} />)
    const card = container.firstChild
    expect(card).toHaveClass('border-red-500/30')
    expect(card).toHaveClass('bg-red-500/5')
  })

  it('applies green color for low latency', () => {
    render(<SystemHealthCard health={mockHealthy} />)
    const latency = screen.getByText('45ms')
    expect(latency).toHaveClass('text-green-600')
  })

  it('applies yellow color for medium latency', () => {
    render(<SystemHealthCard health={mockDegraded} />)
    const latency = screen.getByText('150ms')
    expect(latency).toHaveClass('text-yellow-600')
  })

  it('applies red color for high latency', () => {
    const highLatency = { ...mockHealthy, latency: 500 }
    render(<SystemHealthCard health={highLatency} />)
    const latency = screen.getByText('500ms')
    expect(latency).toHaveClass('text-red-600')
  })
})

describe('AgentStatusGrid', () => {
  it('renders without crashing', () => {
    render(<AgentStatusGrid />)
  })

  it('renders cluster names from mock data', () => {
    render(<AgentStatusGrid />)
    expect(screen.getByText('Discovery')).toBeInTheDocument()
    expect(screen.getByText('Data Architect')).toBeInTheDocument()
    expect(screen.getByText('App Builder')).toBeInTheDocument()
  })

  it('renders instance counts', () => {
    render(<AgentStatusGrid />)
    expect(screen.getByText(/3\/5 instances active/)).toBeInTheDocument()
    expect(screen.getByText(/2\/3 instances active/)).toBeInTheDocument()
    expect(screen.getByText(/0\/4 instances active/)).toBeInTheDocument()
  })

  it('renders tasks in queue', () => {
    render(<AgentStatusGrid />)
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders CPU usage', () => {
    render(<AgentStatusGrid />)
    const cpuLabels = screen.getAllByText('CPU')
    expect(cpuLabels.length).toBe(3)
  })

  it('renders Memory usage', () => {
    render(<AgentStatusGrid />)
    const memoryLabels = screen.getAllByText('Memory')
    expect(memoryLabels.length).toBe(3)
  })

  it('renders View Details buttons', () => {
    render(<AgentStatusGrid />)
    const viewDetailsButtons = screen.getAllByRole('link', { name: 'View Details' })
    expect(viewDetailsButtons.length).toBe(3)
  })

  it('links to correct detail pages', () => {
    render(<AgentStatusGrid />)
    const links = screen.getAllByRole('link', { name: 'View Details' })
    expect(links[0]).toHaveAttribute('href', '/admin/agents/discovery')
    expect(links[1]).toHaveAttribute('href', '/admin/agents/data-architect')
    expect(links[2]).toHaveAttribute('href', '/admin/agents/app-builder')
  })
})

describe('PipelineStatusTable', () => {
  const mockRuns = [
    {
      id: 'run-001',
      pipelineId: 'pl-001',
      pipelineName: 'data-sync-daily',
      status: 'success' as const,
      startTime: '2024-01-15T14:30:00Z',
      duration: 125,
      trigger: 'scheduled' as const,
    },
    {
      id: 'run-002',
      pipelineId: 'pl-002',
      pipelineName: 'ml-feature-pipeline',
      status: 'failed' as const,
      startTime: '2024-01-15T14:15:00Z',
      duration: 45,
      trigger: 'manual' as const,
    },
    {
      id: 'run-003',
      pipelineId: 'pl-003',
      pipelineName: 'running-job',
      status: 'running' as const,
      startTime: '2024-01-15T14:32:00Z',
      duration: null,
      trigger: 'api' as const,
    },
  ]

  it('renders without crashing with default mock data', () => {
    render(<PipelineStatusTable />)
  })

  it('renders provided runs', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    expect(screen.getByText('data-sync-daily')).toBeInTheDocument()
    expect(screen.getByText('ml-feature-pipeline')).toBeInTheDocument()
    expect(screen.getByText('running-job')).toBeInTheDocument()
  })

  it('renders pipeline names as links', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    const links = screen.getAllByRole('link')
    expect(links[0]).toHaveAttribute('href', '/admin/pipelines/pl-001')
    expect(links[1]).toHaveAttribute('href', '/admin/pipelines/pl-002')
  })

  it('renders trigger type', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    expect(screen.getByText('scheduled')).toBeInTheDocument()
    expect(screen.getByText('manual')).toBeInTheDocument()
    expect(screen.getByText('api')).toBeInTheDocument()
  })

  it('renders duration for completed runs', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    expect(screen.getByText('2m 5s')).toBeInTheDocument()
    expect(screen.getByText('45s')).toBeInTheDocument()
  })

  it('shows Running... for running pipelines', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    expect(screen.getByText('Running...')).toBeInTheDocument()
  })

  it('applies red border for failed status', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    // The failed run should have red border styling
    const failedRun = screen.getByText('ml-feature-pipeline').closest('div.flex')?.parentElement
    expect(failedRun).toHaveClass('border-red-500/30')
    expect(failedRun).toHaveClass('bg-red-500/5')
  })

  it('applies blue border for running status', () => {
    render(<PipelineStatusTable runs={mockRuns} />)
    // The running run should have blue border styling
    const runningRun = screen.getByText('running-job').closest('div.flex')?.parentElement
    expect(runningRun).toHaveClass('border-blue-500/30')
    expect(runningRun).toHaveClass('bg-blue-500/5')
  })

  it('shows empty state when no runs', () => {
    render(<PipelineStatusTable runs={[]} />)
    expect(screen.getByText('No recent pipeline runs')).toBeInTheDocument()
  })

  it('limits to 5 runs in compact mode', () => {
    const manyRuns = Array.from({ length: 10 }, (_, i) => ({
      id: `run-${i}`,
      pipelineId: `pl-${i}`,
      pipelineName: `pipeline-${i}`,
      status: 'success' as const,
      startTime: '2024-01-15T14:30:00Z',
      duration: 100,
      trigger: 'scheduled' as const,
    }))

    render(<PipelineStatusTable runs={manyRuns} compact />)

    const links = screen.getAllByRole('link')
    expect(links.length).toBe(5)
  })

  it('shows all runs when not in compact mode', () => {
    const manyRuns = Array.from({ length: 10 }, (_, i) => ({
      id: `run-${i}`,
      pipelineId: `pl-${i}`,
      pipelineName: `pipeline-${i}`,
      status: 'success' as const,
      startTime: '2024-01-15T14:30:00Z',
      duration: 100,
      trigger: 'scheduled' as const,
    }))

    render(<PipelineStatusTable runs={manyRuns} />)

    const links = screen.getAllByRole('link')
    expect(links.length).toBe(10)
  })
})
