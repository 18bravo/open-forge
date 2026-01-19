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
import { useAllAgentTasks } from '@/lib/hooks/use-agent';
import type { AgentTaskStatus } from '@/lib/api';

export default function AgentTasksPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [clusterFilter, setClusterFilter] = React.useState<string>('all');
  const [currentPage, setCurrentPage] = React.useState(1);
  const tasksPerPage = 15;

  const {
    data: tasksData,
    isLoading,
    isError,
    error,
    refetch,
  } = useAllAgentTasks({
    page: currentPage,
    page_size: tasksPerPage,
    status: statusFilter !== 'all' ? (statusFilter as AgentTaskStatus) : undefined,
    cluster: clusterFilter !== 'all' ? clusterFilter : undefined,
  });

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const tasks = tasksData?.items ?? [];
  const totalPages = tasksData?.total_pages ?? 1;
  const totalTasks = tasksData?.total ?? 0;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(tasks, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `agent-tasks-${new Date().toISOString()}.json`;
    link.click();
  };

  // Filter locally by search query (API handles status and cluster)
  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      searchQuery === '' ||
      task.task_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'running':
        return 'bg-blue-500';
      case 'failed':
        return 'bg-red-500';
      case 'queued':
      case 'pending':
        return 'bg-yellow-500';
      case 'cancelled':
        return 'bg-gray-500';
      case 'waiting_approval':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Calculate stats from current page data (would ideally come from API)
  const stats = {
    total: totalTasks,
    completed: tasks.filter((t) => t.status === 'completed').length,
    running: tasks.filter((t) => t.status === 'running').length,
    failed: tasks.filter((t) => t.status === 'failed').length,
    queued: tasks.filter((t) => t.status === 'queued' || t.status === 'pending').length,
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading agent tasks...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    const errorMessage = (error as Error)?.message || 'Failed to load tasks';
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-destructive">Error: {errorMessage}</p>
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href="/admin/agents">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Agents
              </Link>
            </Button>
            <Button variant="outline" onClick={handleRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </div>
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
            <Link href="/admin/agents">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Agent Tasks</h1>
            <p className="text-muted-foreground">
              View and manage all agent tasks across the system
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw
              className={cn('mr-2 h-4 w-4', isRefreshing && 'animate-spin')}
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
            <p className="text-xs text-muted-foreground">Total Tasks</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-xs text-muted-foreground">Completed (this page)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-blue-600">{stats.running}</div>
              <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />
            </div>
            <p className="text-xs text-muted-foreground">Running (this page)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground">Failed (this page)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-yellow-600">{stats.queued}</div>
              <Clock className="h-5 w-5 text-yellow-500" />
            </div>
            <p className="text-xs text-muted-foreground">Queued (this page)</p>
          </CardContent>
        </Card>
      </div>

      {/* Tasks Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Task History</CardTitle>
              <CardDescription>
                Showing {filteredTasks.length} of {totalTasks} tasks
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search tasks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="running">Running</option>
                <option value="failed">Failed</option>
                <option value="queued">Queued</option>
                <option value="pending">Pending</option>
                <option value="waiting_approval">Waiting Approval</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <select
                value={clusterFilter}
                onChange={(e) => {
                  setClusterFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Clusters</option>
                <option value="discovery">Discovery</option>
                <option value="data-architect">Data Architect</option>
                <option value="app-builder">App Builder</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left text-sm font-medium">Task ID</th>
                  <th className="p-3 text-left text-sm font-medium">Type</th>
                  <th className="p-3 text-left text-sm font-medium">Engagement</th>
                  <th className="p-3 text-left text-sm font-medium">Status</th>
                  <th className="p-3 text-left text-sm font-medium">Iteration</th>
                  <th className="p-3 text-left text-sm font-medium">Created</th>
                  <th className="p-3 text-left text-sm font-medium">Completed</th>
                </tr>
              </thead>
              <tbody>
                {filteredTasks.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                      {searchQuery || statusFilter !== 'all' || clusterFilter !== 'all'
                        ? 'No tasks match your filters'
                        : 'No tasks found'}
                    </td>
                  </tr>
                ) : (
                  filteredTasks.map((task) => (
                    <tr key={task.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="p-3">
                        <p className="font-mono text-sm">{task.id.slice(0, 8)}...</p>
                      </td>
                      <td className="p-3">
                        <code className="rounded bg-muted px-2 py-1 text-xs">
                          {task.task_type}
                        </code>
                      </td>
                      <td className="p-3">
                        <Link
                          href={`/engagements/${task.engagement_id}`}
                          className="text-primary hover:underline font-mono text-sm"
                        >
                          {task.engagement_id.slice(0, 8)}...
                        </Link>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div
                            className={cn(
                              'h-2 w-2 rounded-full',
                              getStatusColor(task.status)
                            )}
                          />
                          <span className="text-sm capitalize">{task.status.replace('_', ' ')}</span>
                        </div>
                      </td>
                      <td className="p-3 text-sm">{task.current_iteration}</td>
                      <td className="p-3 text-sm text-muted-foreground">
                        {new Date(task.created_at).toLocaleString()}
                      </td>
                      <td className="p-3 text-sm text-muted-foreground">
                        {task.completed_at
                          ? new Date(task.completed_at).toLocaleString()
                          : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
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
