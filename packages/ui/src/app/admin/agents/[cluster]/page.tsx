'use client';

import * as React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  AlertCircle,
  ArrowLeft,
  Bot,
  CheckCircle2,
  Clock,
  Cpu,
  History,
  Loader2,
  MemoryStick,
  Minus,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Settings,
  Trash2,
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
import { MetricsChart } from '@/components/admin/MetricsChart';
import { useAgentCluster, useScaleCluster } from '@/lib/hooks/use-agent-cluster';

export default function ClusterDetailPage() {
  const params = useParams();
  const clusterSlug = params.cluster as string;
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const {
    data: cluster,
    isLoading,
    isError,
    error,
    refetch,
  } = useAgentCluster(clusterSlug);

  const scaleCluster = useScaleCluster();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  const handleScaleUp = () => {
    if (cluster) {
      const newTarget = Math.min(cluster.instance_count + 1, cluster.config.max_instances);
      scaleCluster.mutate({ slug: clusterSlug, targetInstances: newTarget });
    }
  };

  const handleScaleDown = () => {
    if (cluster) {
      const newTarget = Math.max(cluster.instance_count - 1, cluster.config.min_instances);
      scaleCluster.mutate({ slug: clusterSlug, targetInstances: newTarget });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500';
      case 'idle':
        return 'bg-yellow-500';
      case 'stopped':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'queued':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading cluster details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    const errorMessage = (error as Error)?.message || 'Failed to load cluster';
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

  if (!cluster) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <AlertCircle className="h-8 w-8 text-muted-foreground" />
          <p className="text-muted-foreground">Cluster not found</p>
          <Button variant="outline" asChild>
            <Link href="/admin/agents">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Agents
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const instances = cluster.instances ?? [];
  const activeInstances = instances.filter((i) => i.status === 'running' || i.status === 'idle').length;
  const avgCpuUsage = activeInstances > 0
    ? Math.round(
        instances
          .filter((i) => i.status === 'running' || i.status === 'idle')
          .reduce((acc, i) => acc + i.cpu_usage, 0) / activeInstances
      )
    : 0;
  const avgMemoryUsage = activeInstances > 0
    ? Math.round(
        instances
          .filter((i) => i.status === 'running' || i.status === 'idle')
          .reduce((acc, i) => acc + i.memory_usage, 0) / activeInstances
      )
    : 0;

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
            <h1 className="text-3xl font-bold tracking-tight">{cluster.name}</h1>
            <p className="text-muted-foreground">{cluster.description}</p>
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
          <Button variant="outline" size="sm">
            <Settings className="mr-2 h-4 w-4" />
            Configure
          </Button>
          <div className="flex items-center border rounded-md">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleScaleDown}
              disabled={scaleCluster.isPending || cluster.instance_count <= cluster.config.min_instances}
              className="rounded-r-none"
            >
              <Minus className="h-4 w-4" />
            </Button>
            <span className="px-3 text-sm font-medium border-x">
              {cluster.instance_count}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleScaleUp}
              disabled={scaleCluster.isPending || cluster.instance_count >= cluster.config.max_instances}
              className="rounded-l-none"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Instances</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeInstances}/{instances.length}</div>
            <p className="text-xs text-muted-foreground">
              {cluster.config.auto_scale ? 'Auto-scaling enabled' : 'Manual scaling'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Queued Tasks</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cluster.queued_tasks}</div>
            <p className="text-xs text-muted-foreground">
              Tasks waiting for processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgCpuUsage}%</div>
            <p className="text-xs text-muted-foreground">
              Across active instances
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Memory</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgMemoryUsage}%</div>
            <p className="text-xs text-muted-foreground">
              Across active instances
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Metrics Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cluster Metrics</CardTitle>
          <CardDescription>
            Resource utilization and task throughput over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <MetricsChart />
        </CardContent>
      </Card>

      {/* Instances */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Agent Instances</CardTitle>
              <CardDescription>
                Individual agents in this cluster
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/admin/agents/tasks">
                <History className="mr-2 h-4 w-4" />
                View All Tasks
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {instances.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Bot className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No instances in this cluster</p>
            </div>
          ) : (
            <div className="space-y-3">
              {instances.map((instance) => (
                <div
                  key={instance.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'h-3 w-3 rounded-full',
                        getStatusColor(instance.status)
                      )}
                    />
                    <div>
                      <p className="font-medium">{instance.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {instance.current_task || `Status: ${instance.status}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {(instance.status === 'running' || instance.status === 'idle') && (
                      <>
                        <div className="text-right text-xs text-muted-foreground">
                          <div>CPU: {instance.cpu_usage}%</div>
                          <div>MEM: {instance.memory_usage}%</div>
                        </div>
                        <Button variant="ghost" size="icon" title="Pause">
                          <Pause className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                    {instance.status === 'stopped' && (
                      <Button variant="ghost" size="icon" title="Start">
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    {instance.status === 'error' && (
                      <Button variant="ghost" size="icon" title="Restart">
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    )}
                    <Button variant="ghost" size="icon" title="Remove">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Cluster Configuration</CardTitle>
              <CardDescription>
                Current settings for this cluster
              </CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              Edit Configuration
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Max Instances</div>
              <div className="text-2xl font-bold">{cluster.config.max_instances}</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Min Instances</div>
              <div className="text-2xl font-bold">{cluster.config.min_instances}</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Auto-Scale</div>
              <div className="text-2xl font-bold">{cluster.config.auto_scale ? 'Enabled' : 'Disabled'}</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Scale Up Threshold</div>
              <div className="text-2xl font-bold">{cluster.config.scale_up_threshold}%</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Scale Down Threshold</div>
              <div className="text-2xl font-bold">{cluster.config.scale_down_threshold}%</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Agent Types</div>
              <div className="text-2xl font-bold">{cluster.agent_types?.length ?? 0}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
