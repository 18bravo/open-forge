'use client';

import * as React from 'react';
import Link from 'next/link';
import { CheckCircle2, Clock, RefreshCw, XCircle } from 'lucide-react';

import { cn } from '@/lib/utils';

interface PipelineRun {
  id: string;
  pipelineId: string;
  pipelineName: string;
  status: 'success' | 'failed' | 'running' | 'queued';
  startTime: string;
  duration: number | null;
  trigger: 'scheduled' | 'manual' | 'api';
}

interface PipelineStatusTableProps {
  compact?: boolean;
  runs?: PipelineRun[];
}

export function PipelineStatusTable({ compact = false, runs: externalRuns }: PipelineStatusTableProps) {
  // Mock data - in production, this would come from props or API calls
  const [runs, setRuns] = React.useState<PipelineRun[]>(
    externalRuns || [
      {
        id: 'run-001',
        pipelineId: 'pl-001',
        pipelineName: 'data-sync-daily',
        status: 'success',
        startTime: '2024-01-15T14:30:00Z',
        duration: 1245,
        trigger: 'scheduled',
      },
      {
        id: 'run-002',
        pipelineId: 'pl-002',
        pipelineName: 'ml-feature-pipeline',
        status: 'running',
        startTime: '2024-01-15T14:32:00Z',
        duration: null,
        trigger: 'scheduled',
      },
      {
        id: 'run-003',
        pipelineId: 'pl-007',
        pipelineName: 'log-aggregation',
        status: 'success',
        startTime: '2024-01-15T14:15:00Z',
        duration: 89,
        trigger: 'scheduled',
      },
      {
        id: 'run-004',
        pipelineId: 'pl-005',
        pipelineName: 'data-quality-checks',
        status: 'failed',
        startTime: '2024-01-15T14:00:00Z',
        duration: 45,
        trigger: 'scheduled',
      },
      {
        id: 'run-005',
        pipelineId: 'pl-003',
        pipelineName: 'analytics-refresh',
        status: 'queued',
        startTime: '-',
        duration: null,
        trigger: 'manual',
      },
    ]
  );

  // Simulate real-time updates for running pipelines
  React.useEffect(() => {
    const interval = setInterval(() => {
      setRuns((prev) =>
        prev.map((run) => {
          if (run.status === 'running' && Math.random() > 0.8) {
            return { ...run, status: 'success' as const, duration: Math.floor(Math.random() * 300) + 60 };
          }
          return run;
        })
      );
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
      case 'queued':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500/10 text-green-600';
      case 'failed':
        return 'bg-red-500/10 text-red-600';
      case 'running':
        return 'bg-blue-500/10 text-blue-600';
      case 'queued':
        return 'bg-yellow-500/10 text-yellow-600';
      default:
        return 'bg-gray-500/10 text-gray-600';
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const formatTime = (timeStr: string) => {
    if (timeStr === '-') return 'Pending';
    const date = new Date(timeStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const displayRuns = compact ? runs.slice(0, 5) : runs;

  return (
    <div className="space-y-2">
      {displayRuns.map((run) => (
        <div
          key={run.id}
          className={cn(
            'flex items-center justify-between rounded-lg border p-3',
            run.status === 'failed' && 'border-red-500/30 bg-red-500/5',
            run.status === 'running' && 'border-blue-500/30 bg-blue-500/5'
          )}
        >
          <div className="flex items-center gap-3">
            {getStatusIcon(run.status)}
            <div>
              <Link
                href={`/admin/pipelines/${run.pipelineId}`}
                className="font-medium hover:underline text-sm"
              >
                {run.pipelineName}
              </Link>
              <p className="text-xs text-muted-foreground capitalize">
                {run.trigger}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right text-xs">
              <p className="text-muted-foreground">{formatTime(run.startTime)}</p>
              <p className={cn('font-medium', getStatusBadge(run.status))}>
                {run.status === 'running'
                  ? 'Running...'
                  : run.status === 'queued'
                    ? 'Queued'
                    : formatDuration(run.duration)}
              </p>
            </div>
          </div>
        </div>
      ))}

      {runs.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No recent pipeline runs
        </div>
      )}
    </div>
  );
}
