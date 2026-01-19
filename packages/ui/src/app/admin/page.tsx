'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  RefreshCw,
  Server,
  Users,
  Workflow,
  XCircle,
  Loader2,
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
import { SystemHealthCard } from '@/components/admin/SystemHealthCard';
import { AgentStatusGrid } from '@/components/admin/AgentStatusGrid';
import { PipelineStatusTable } from '@/components/admin/PipelineStatusTable';
import { MetricsChart } from '@/components/admin/MetricsChart';
import { useSystemHealth, useDashboardStats, useRecentAlerts } from '@/lib/hooks/use-admin';

export default function AdminDashboardPage() {
  const [lastUpdated, setLastUpdated] = React.useState<Date>(new Date());

  // Fetch data using hooks
  const {
    data: healthData,
    isLoading: isHealthLoading,
    isError: isHealthError,
    refetch: refetchHealth,
  } = useSystemHealth();

  const {
    data: statsData,
    isLoading: isStatsLoading,
    isError: isStatsError,
    refetch: refetchStats,
  } = useDashboardStats();

  const {
    data: alertsData,
    isLoading: isAlertsLoading,
    isError: isAlertsError,
    refetch: refetchAlerts,
  } = useRecentAlerts(10);

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refetchHealth(), refetchStats(), refetchAlerts()]);
    setLastUpdated(new Date());
    setIsRefreshing(false);
  };

  // Update lastUpdated when data changes
  React.useEffect(() => {
    if (healthData || statsData || alertsData) {
      setLastUpdated(new Date());
    }
  }, [healthData, statsData, alertsData]);

  // Derived values from health data
  const systemHealth = healthData?.services || [];
  const healthyServices = systemHealth.filter((s) => s.status === 'healthy').length;
  const totalServices = systemHealth.length;

  // Derived values from stats data
  const engagementSummary = statsData?.engagements || {
    total: 0,
    active: 0,
    pending: 0,
    completed: 0,
  };
  const agentStats = statsData?.agents || {
    total_clusters: 0,
    running_instances: 0,
    queued_tasks: 0,
  };

  // Recent alerts
  const recentAlerts = alertsData || [];

  // Loading state component
  const LoadingCard = () => (
    <div className="flex items-center justify-center py-8">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );

  // Error state component
  const ErrorCard = ({ onRetry }: { onRetry: () => void }) => (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <XCircle className="h-8 w-8 text-destructive mb-2" />
      <p className="text-sm text-muted-foreground mb-2">Failed to load data</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCw className="mr-2 h-4 w-4" />
        Retry
      </Button>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            System overview and monitoring for Open Forge
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
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
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isHealthLoading ? (
              <LoadingCard />
            ) : isHealthError ? (
              <ErrorCard onRetry={() => refetchHealth()} />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {healthyServices}/{totalServices}
                </div>
                <p className="text-xs text-muted-foreground">
                  Services operational
                </p>
                <div className="mt-2 flex gap-1">
                  {systemHealth.map((service) => (
                    <div
                      key={service.service}
                      className={cn(
                        'h-2 flex-1 rounded-full',
                        service.status === 'healthy' && 'bg-green-500',
                        service.status === 'degraded' && 'bg-yellow-500',
                        service.status === 'unhealthy' && 'bg-red-500'
                      )}
                      title={`${service.service}: ${service.status}`}
                    />
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Engagements</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isStatsLoading ? (
              <LoadingCard />
            ) : isStatsError ? (
              <ErrorCard onRetry={() => refetchStats()} />
            ) : (
              <>
                <div className="text-2xl font-bold">{engagementSummary.active}</div>
                <p className="text-xs text-muted-foreground">
                  {engagementSummary.pending} pending, {engagementSummary.total} total
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agent Clusters</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isStatsLoading ? (
              <LoadingCard />
            ) : isStatsError ? (
              <ErrorCard onRetry={() => refetchStats()} />
            ) : (
              <>
                <div className="text-2xl font-bold">{agentStats.total_clusters}</div>
                <p className="text-xs text-muted-foreground">
                  {agentStats.running_instances} running, {agentStats.queued_tasks} queued
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Workflow className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isStatsLoading ? (
              <LoadingCard />
            ) : isStatsError ? (
              <ErrorCard onRetry={() => refetchStats()} />
            ) : (
              <>
                <div className="text-2xl font-bold">{statsData?.approvals.pending || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {statsData?.approvals.approved_today || 0} approved today, {statsData?.approvals.rejected_today || 0} rejected
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* System Health Details */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>System Health</CardTitle>
                <CardDescription>
                  Real-time status of all system services
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/settings">
                  View Details
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isHealthLoading ? (
              <LoadingCard />
            ) : isHealthError ? (
              <ErrorCard onRetry={() => refetchHealth()} />
            ) : (
              <div className="space-y-3">
                {systemHealth.map((service) => (
                  <SystemHealthCard key={service.service} health={service} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Agent Clusters</CardTitle>
                <CardDescription>
                  Status overview of all agent clusters
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/agents">
                  Manage Agents
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <AgentStatusGrid />
          </CardContent>
        </Card>
      </div>

      {/* Metrics Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>System Metrics</CardTitle>
              <CardDescription>
                Resource utilization over the last 24 hours
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <MetricsChart />
        </CardContent>
      </Card>

      {/* Recent Alerts and Pipeline Status */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Alerts</CardTitle>
                <CardDescription>
                  System alerts and notifications
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/settings/audit">
                  View All
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isAlertsLoading ? (
              <LoadingCard />
            ) : isAlertsError ? (
              <ErrorCard onRetry={() => refetchAlerts()} />
            ) : recentAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Activity className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No recent alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={cn(
                      'flex items-start gap-3 rounded-lg border p-3',
                      alert.severity === 'critical' && 'border-red-500/50 bg-red-500/10',
                      alert.severity === 'warning' && 'border-yellow-500/50 bg-yellow-500/10',
                      alert.severity === 'info' && 'border-blue-500/50 bg-blue-500/10'
                    )}
                  >
                    {alert.severity === 'critical' && (
                      <XCircle className="h-5 w-5 shrink-0 text-red-500" />
                    )}
                    {alert.severity === 'warning' && (
                      <AlertTriangle className="h-5 w-5 shrink-0 text-yellow-500" />
                    )}
                    {alert.severity === 'info' && (
                      <Activity className="h-5 w-5 shrink-0 text-blue-500" />
                    )}
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium leading-tight">
                        {alert.message}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{alert.source}</span>
                        <span>-</span>
                        <span>
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pipeline Status */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Pipeline Status</CardTitle>
                <CardDescription>
                  Recent pipeline runs and their status
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/pipelines">
                  View All
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <PipelineStatusTable compact />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
