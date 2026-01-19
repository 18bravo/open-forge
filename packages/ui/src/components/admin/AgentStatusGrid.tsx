'use client';

import * as React from 'react';
import Link from 'next/link';
import { Bot, Cpu, Database, MemoryStick, Workflow } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface AgentClusterStatus {
  id: string;
  name: string;
  slug: string;
  status: 'running' | 'idle' | 'stopped' | 'error';
  activeInstances: number;
  totalInstances: number;
  cpuUsage: number;
  memoryUsage: number;
  tasksInQueue: number;
}

export function AgentStatusGrid() {
  // Mock data - in production, this would come from props or API calls with real-time updates
  const [clusters, setClusters] = React.useState<AgentClusterStatus[]>([
    {
      id: '1',
      name: 'Discovery',
      slug: 'discovery',
      status: 'running',
      activeInstances: 3,
      totalInstances: 5,
      cpuUsage: 45,
      memoryUsage: 62,
      tasksInQueue: 12,
    },
    {
      id: '2',
      name: 'Data Architect',
      slug: 'data-architect',
      status: 'running',
      activeInstances: 2,
      totalInstances: 3,
      cpuUsage: 78,
      memoryUsage: 89,
      tasksInQueue: 5,
    },
    {
      id: '3',
      name: 'App Builder',
      slug: 'app-builder',
      status: 'idle',
      activeInstances: 0,
      totalInstances: 4,
      cpuUsage: 5,
      memoryUsage: 23,
      tasksInQueue: 0,
    },
  ]);

  // Simulate real-time updates
  React.useEffect(() => {
    const interval = setInterval(() => {
      setClusters((prev) =>
        prev.map((cluster) => ({
          ...cluster,
          cpuUsage: Math.min(100, Math.max(0, cluster.cpuUsage + (Math.random() - 0.5) * 10)),
          memoryUsage: Math.min(100, Math.max(0, cluster.memoryUsage + (Math.random() - 0.5) * 5)),
        }))
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

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

  const getUsageColor = (usage: number) => {
    if (usage > 80) return 'bg-red-500';
    if (usage > 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-4">
      {clusters.map((cluster) => {
        const ClusterIcon = getClusterIcon(cluster.slug);
        return (
          <div
            key={cluster.id}
            className="rounded-lg border p-4 hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <ClusterIcon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{cluster.name}</p>
                    <div
                      className={cn(
                        'h-2 w-2 rounded-full',
                        getStatusColor(cluster.status)
                      )}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {cluster.activeInstances}/{cluster.totalInstances} instances active
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">{cluster.tasksInQueue}</p>
                <p className="text-xs text-muted-foreground">in queue</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1 text-muted-foreground">
                    <Cpu className="h-3 w-3" /> CPU
                  </span>
                  <span>{Math.round(cluster.cpuUsage)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-secondary">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-500',
                      getUsageColor(cluster.cpuUsage)
                    )}
                    style={{ width: `${cluster.cpuUsage}%` }}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1 text-muted-foreground">
                    <MemoryStick className="h-3 w-3" /> Memory
                  </span>
                  <span>{Math.round(cluster.memoryUsage)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-secondary">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-500',
                      getUsageColor(cluster.memoryUsage)
                    )}
                    style={{ width: `${cluster.memoryUsage}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t">
              <Button variant="ghost" size="sm" className="w-full" asChild>
                <Link href={`/admin/agents/${cluster.slug}`}>
                  View Details
                </Link>
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
