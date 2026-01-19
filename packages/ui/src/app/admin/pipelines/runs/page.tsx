'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Download,
  Loader2,
  RefreshCw,
  Search,
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
import { usePipelineRuns } from '@/lib/hooks/use-pipeline';
import type { PipelineRunStatus } from '@/lib/api';

export default function PipelineRunsPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [page, setPage] = React.useState(1);
  const pageSize = 20;

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isRefetching,
  } = usePipelineRuns({
    page,
    page_size: pageSize,
    status: statusFilter !== 'all' ? statusFilter as PipelineRunStatus : undefined,
  });

  const runs = data?.items ?? [];

  const filteredRuns = runs.filter((run) => {
    const matchesSearch =
      run.pipeline_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      run.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      run.triggered_by.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const handleExport = () => {
    const dataStr = JSON.stringify(filteredRuns, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pipeline-runs-${new Date().toISOString()}.json`;
    link.click();
  };

  const getStatusIcon = (status: PipelineRunStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: PipelineRunStatus) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/10 text-green-600 border-green-500/30';
      case 'failed':
        return 'bg-red-500/10 text-red-600 border-red-500/30';
      case 'running':
        return 'bg-blue-500/10 text-blue-600 border-blue-500/30';
      case 'cancelled':
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/30';
      default:
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${minutes}m ${secs}s`;
    }
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Stats computed from current data
  const stats = {
    total: data?.total ?? 0,
    completed: runs.filter((r) => r.status === 'completed').length,
    running: runs.filter((r) => r.status === 'running').length,
    failed: runs.filter((r) => r.status === 'failed').length,
    pending: runs.filter((r) => r.status === 'pending').length,
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading pipeline runs...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-center">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm font-medium">Failed to load pipeline runs</p>
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
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/admin/pipelines">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Pipeline Runs</h1>
            <p className="text-muted-foreground">
              View all pipeline executions across the system
            </p>
          </div>
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
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Total Runs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-blue-600">{stats.running}</div>
              <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />
            </div>
            <p className="text-xs text-muted-foreground">Running</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground">Failed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
              <Clock className="h-5 w-5 text-yellow-500" />
            </div>
            <p className="text-xs text-muted-foreground">Pending</p>
          </CardContent>
        </Card>
      </div>

      {/* Runs Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>All Runs</CardTitle>
              <CardDescription>
                Showing {filteredRuns.length} of {data?.total ?? 0} pipeline runs
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search runs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="running">Running</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredRuns.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No pipeline runs found
            </div>
          ) : (
            <div className="rounded-md border overflow-x-auto">
              <table className="w-full min-w-[800px]">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="p-3 text-left text-sm font-medium">Status</th>
                    <th className="p-3 text-left text-sm font-medium">Pipeline</th>
                    <th className="p-3 text-left text-sm font-medium">Run #</th>
                    <th className="p-3 text-left text-sm font-medium">Triggered By</th>
                    <th className="p-3 text-left text-sm font-medium">Started</th>
                    <th className="p-3 text-left text-sm font-medium">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRuns.map((run) => (
                    <tr key={run.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(run.status)}
                          <span
                            className={cn(
                              'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
                              getStatusColor(run.status)
                            )}
                          >
                            {run.status}
                          </span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Link
                          href={`/admin/pipelines/${run.pipeline_id}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {run.pipeline_name}
                        </Link>
                      </td>
                      <td className="p-3 text-sm">#{run.run_number}</td>
                      <td className="p-3 text-sm text-muted-foreground">
                        {run.triggered_by}
                      </td>
                      <td className="p-3 text-sm text-muted-foreground">
                        {new Date(run.started_at).toLocaleString()}
                      </td>
                      <td className="p-3 text-sm">{formatDuration(run.duration_seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
