'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Bot,
  Cpu,
  Database,
  Loader2,
  MemoryStick,
  MoreVertical,
  Play,
  Power,
  RefreshCw,
  Settings,
  Workflow,
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
import { useAgentClusters, useAgentTypes } from '@/lib/hooks/use-agent-cluster';

export default function AgentsPage() {
  const [searchQuery, setSearchQuery] = React.useState('');

  const {
    data: clustersData,
    isLoading: isLoadingClusters,
    isError: isErrorClusters,
    error: clustersError,
    refetch: refetchClusters,
  } = useAgentClusters();

  const {
    data: agentTypesData,
    isLoading: isLoadingTypes,
    isError: isErrorTypes,
    error: typesError,
    refetch: refetchTypes,
  } = useAgentTypes();

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const clusters = clustersData?.items ?? [];
  const agentTypes = agentTypesData ?? [];

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refetchClusters(), refetchTypes()]);
    setIsRefreshing(false);
  };

  const filteredAgentTypes = agentTypes.filter(
    (agent) =>
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.cluster.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.task_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
        return 'bg-green-500';
      case 'idle':
        return 'bg-yellow-500';
      case 'stopped':
      case 'inactive':
      case 'offline':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getClusterIcon = (slug: string) => {
    switch (slug) {
      case 'discovery':
        return Database;
      case 'data-architect':
        return Workflow;
      case 'app-builder':
        return Bot;
      default:
        return Bot;
    }
  };

  // Loading state
  if (isLoadingClusters || isLoadingTypes) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading agent clusters...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (isErrorClusters || isErrorTypes) {
    const errorMessage = (clustersError as Error)?.message || (typesError as Error)?.message || 'Failed to load data';
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-destructive">Error: {errorMessage}</p>
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
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
          <h1 className="text-3xl font-bold tracking-tight">Agent Management</h1>
          <p className="text-muted-foreground">
            Monitor and manage AI agent clusters and tasks
          </p>
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
          <Button asChild>
            <Link href="/admin/agents/tasks">
              <Activity className="mr-2 h-4 w-4" />
              View All Tasks
            </Link>
          </Button>
        </div>
      </div>

      {/* Cluster Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {clusters.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Bot className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No agent clusters found</p>
            </CardContent>
          </Card>
        ) : (
          clusters.map((cluster) => {
            const ClusterIcon = getClusterIcon(cluster.slug);
            return (
              <Card key={cluster.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <ClusterIcon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{cluster.name}</CardTitle>
                        <div className="flex items-center gap-2 mt-1">
                          <div
                            className={cn(
                              'h-2 w-2 rounded-full',
                              getStatusColor(cluster.status)
                            )}
                          />
                          <span className="text-xs capitalize text-muted-foreground">
                            {cluster.status}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" asChild>
                      <Link href={`/admin/agents/${cluster.slug}`}>
                        <Settings className="h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pb-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Bot className="h-4 w-4" />
                        Instances
                      </div>
                      <p className="text-xl font-semibold">
                        {cluster.instance_count}/{cluster.max_instances}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Activity className="h-4 w-4" />
                        Queue
                      </div>
                      <p className="text-xl font-semibold">{cluster.queued_tasks}</p>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-muted-foreground">
                        <Cpu className="h-4 w-4" /> CPU
                      </span>
                      <span className="font-medium">{cluster.cpu_usage}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-secondary">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all',
                          cluster.cpu_usage > 80
                            ? 'bg-red-500'
                            : cluster.cpu_usage > 60
                              ? 'bg-yellow-500'
                              : 'bg-green-500'
                        )}
                        style={{ width: `${cluster.cpu_usage}%` }}
                      />
                    </div>
                  </div>
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-muted-foreground">
                        <MemoryStick className="h-4 w-4" /> Memory
                      </span>
                      <span className="font-medium">{cluster.memory_usage}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-secondary">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all',
                          cluster.memory_usage > 80
                            ? 'bg-red-500'
                            : cluster.memory_usage > 60
                              ? 'bg-yellow-500'
                              : 'bg-green-500'
                        )}
                        style={{ width: `${cluster.memory_usage}%` }}
                      />
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-end border-t pt-4">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/admin/agents/${cluster.slug}`}>
                        Details
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Agent Types Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Agent Types</CardTitle>
              <CardDescription>
                All configured agent types across clusters
              </CardDescription>
            </div>
            <div className="w-64">
              <Input
                placeholder="Search agents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left text-sm font-medium">Agent Name</th>
                  <th className="p-3 text-left text-sm font-medium">Cluster</th>
                  <th className="p-3 text-left text-sm font-medium">Task Type</th>
                  <th className="p-3 text-left text-sm font-medium">Version</th>
                  <th className="p-3 text-left text-sm font-medium">Status</th>
                  <th className="p-3 text-left text-sm font-medium">Instances</th>
                  <th className="p-3 text-left text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAgentTypes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                      {searchQuery ? 'No agents match your search' : 'No agent types configured'}
                    </td>
                  </tr>
                ) : (
                  filteredAgentTypes.map((agent) => (
                    <tr key={agent.id} className="border-b last:border-0">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Bot className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{agent.name}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Link
                          href={`/admin/agents/${agent.cluster}`}
                          className="text-primary hover:underline capitalize"
                        >
                          {agent.cluster.replace('-', ' ')}
                        </Link>
                      </td>
                      <td className="p-3">
                        <code className="rounded bg-muted px-2 py-1 text-xs">
                          {agent.task_type}
                        </code>
                      </td>
                      <td className="p-3 text-sm text-muted-foreground">
                        v{agent.version}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div
                            className={cn(
                              'h-2 w-2 rounded-full',
                              getStatusColor(agent.status)
                            )}
                          />
                          <span className="text-sm capitalize">{agent.status}</span>
                        </div>
                      </td>
                      <td className="p-3 text-sm">{agent.instance_count}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="icon" title="Start/Stop">
                            {agent.status === 'inactive' ? (
                              <Play className="h-4 w-4" />
                            ) : (
                              <Power className="h-4 w-4" />
                            )}
                          </Button>
                          <Button variant="ghost" size="icon" title="Settings">
                            <Settings className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" title="More">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
