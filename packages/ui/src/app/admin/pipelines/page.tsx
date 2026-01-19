'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Loader2,
  MoreVertical,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Workflow,
  XCircle,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  usePipelines,
  useTriggerPipeline,
  useUpdatePipelineStatus,
} from '@/lib/hooks/use-pipeline';
import type { PipelineSummary, PipelineStatus, PipelineRunStatus } from '@/lib/api';

export default function PipelinesPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [page, setPage] = React.useState(1);

  const { data, isLoading, isError, error, refetch, isRefetching } = usePipelines({
    page,
    page_size: 20,
    active_only: statusFilter === 'active' ? true : undefined,
  });

  const triggerPipeline = useTriggerPipeline();
  const updateStatus = useUpdatePipelineStatus();

  const pipelines = data?.items ?? [];

  const filteredPipelines = pipelines.filter((pipeline) => {
    const matchesSearch =
      pipeline.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pipeline.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || pipeline.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: PipelineStatus) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'paused':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      case 'disabled':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getRunStatusIcon = (status: PipelineRunStatus | null) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatSchedule = (cron: string | null) => {
    if (!cron) return 'No schedule';
    // Simple cron to human-readable conversion
    if (cron === '0 2 * * *') return 'Daily at 2:00 AM';
    if (cron === '0 */4 * * *') return 'Every 4 hours';
    if (cron === '0 6 * * *') return 'Daily at 6:00 AM';
    if (cron === '0 0 * * 0') return 'Weekly on Sunday';
    if (cron === '0 */1 * * *') return 'Every hour';
    if (cron === '0 3 * * *') return 'Daily at 3:00 AM';
    if (cron === '*/15 * * * *') return 'Every 15 minutes';
    if (cron === '0 1 * * *') return 'Daily at 1:00 AM';
    return cron;
  };

  const handleTriggerRun = (pipelineId: string) => {
    triggerPipeline.mutate(pipelineId);
  };

  const handleToggleStatus = (pipeline: PipelineSummary) => {
    const newStatus: PipelineStatus = pipeline.status === 'active' ? 'paused' : 'active';
    updateStatus.mutate({ pipelineId: pipeline.id, status: newStatus });
  };

  // Stats computed from data
  const stats = {
    total: pipelines.length,
    active: pipelines.filter((p) => p.status === 'active').length,
    paused: pipelines.filter((p) => p.status === 'paused').length,
    error: pipelines.filter((p) => p.status === 'error').length,
    running: pipelines.filter((p) => p.last_run_status === 'running').length,
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading pipelines...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-center">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm font-medium">Failed to load pipelines</p>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pipeline Management</h1>
          <p className="text-muted-foreground">
            Configure and monitor data pipelines
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw
              className={cn('mr-2 h-4 w-4', isRefetching && 'animate-spin')}
            />
            Refresh
          </Button>
          <Button asChild>
            <Link href="/admin/pipelines/runs">
              <Activity className="mr-2 h-4 w-4" />
              View All Runs
            </Link>
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Pipeline
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Total Pipelines</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              <div className="h-2 w-2 rounded-full bg-green-500" />
            </div>
            <p className="text-xs text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-blue-600">{stats.running}</div>
              <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
            </div>
            <p className="text-xs text-muted-foreground">Running Now</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-yellow-600">{stats.paused}</div>
              <Pause className="h-4 w-4 text-yellow-500" />
            </div>
            <p className="text-xs text-muted-foreground">Paused</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-red-600">{stats.error}</div>
              <XCircle className="h-4 w-4 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground">Error</p>
          </CardContent>
        </Card>
      </div>

      {/* Pipelines Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>All Pipelines</CardTitle>
              <CardDescription>
                Showing {filteredPipelines.length} pipelines
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search pipelines..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="error">Error</option>
                <option value="disabled">Disabled</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredPipelines.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No pipelines found
            </div>
          ) : (
            <div className="space-y-4">
              {filteredPipelines.map((pipeline) => (
                <div
                  key={pipeline.id}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-lg',
                        pipeline.status === 'active' && 'bg-green-500/10',
                        pipeline.status === 'paused' && 'bg-yellow-500/10',
                        pipeline.status === 'error' && 'bg-red-500/10',
                        pipeline.status === 'disabled' && 'bg-gray-500/10'
                      )}
                    >
                      <Workflow
                        className={cn(
                          'h-5 w-5',
                          pipeline.status === 'active' && 'text-green-500',
                          pipeline.status === 'paused' && 'text-yellow-500',
                          pipeline.status === 'error' && 'text-red-500',
                          pipeline.status === 'disabled' && 'text-gray-500'
                        )}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/admin/pipelines/${pipeline.id}`}
                          className="font-medium hover:underline"
                        >
                          {pipeline.name}
                        </Link>
                        <div
                          className={cn(
                            'h-2 w-2 rounded-full',
                            getStatusColor(pipeline.status)
                          )}
                        />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {pipeline.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-8">
                    <div className="text-right">
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>{formatSchedule(pipeline.schedule)}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Next: {pipeline.next_run
                          ? new Date(pipeline.next_run).toLocaleString()
                          : 'Not scheduled'}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="flex items-center gap-2 text-sm">
                        {getRunStatusIcon(pipeline.last_run_status)}
                        <span>
                          {pipeline.last_run_status === 'running'
                            ? 'Running'
                            : pipeline.last_run_status ?? 'Never run'}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {pipeline.last_run
                          ? `Last: ${new Date(pipeline.last_run).toLocaleString()}`
                          : 'Never run'}
                      </p>
                    </div>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        title={pipeline.status === 'active' ? 'Pause' : 'Resume'}
                        onClick={() => handleToggleStatus(pipeline)}
                        disabled={updateStatus.isPending}
                      >
                        {pipeline.status === 'active' ? (
                          <Pause className="h-4 w-4" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Run Now"
                        onClick={() => handleTriggerRun(pipeline.id)}
                        disabled={triggerPipeline.isPending}
                      >
                        <RefreshCw className={cn('h-4 w-4', triggerPipeline.isPending && 'animate-spin')} />
                      </Button>
                      <Button variant="ghost" size="icon" asChild title="Settings">
                        <Link href={`/admin/pipelines/${pipeline.id}`}>
                          <Settings className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button variant="ghost" size="icon" title="More">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Page {page} of {data.total_pages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
