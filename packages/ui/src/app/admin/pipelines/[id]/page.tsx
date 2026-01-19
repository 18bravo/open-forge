'use client';

import * as React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Code,
  Copy,
  Edit,
  History,
  Loader2,
  Pause,
  Play,
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
import {
  usePipeline,
  usePipelineRuns,
  useTriggerPipeline,
  useUpdatePipelineStatus,
} from '@/lib/hooks/use-pipeline';
import type { PipelineRunStatus, PipelineStatus } from '@/lib/api';

export default function PipelineDetailPage() {
  const params = useParams();
  const pipelineId = params.id as string;
  const [activeTab, setActiveTab] = React.useState<'runs' | 'config' | 'code'>('runs');

  const {
    data: pipeline,
    isLoading: isPipelineLoading,
    isError: isPipelineError,
    error: pipelineError,
    refetch: refetchPipeline,
    isRefetching: isPipelineRefetching,
  } = usePipeline(pipelineId);

  const {
    data: runsData,
    isLoading: isRunsLoading,
    isError: isRunsError,
    refetch: refetchRuns,
    isRefetching: isRunsRefetching,
  } = usePipelineRuns({ pipeline_id: pipelineId });

  const triggerPipeline = useTriggerPipeline();
  const updateStatus = useUpdatePipelineStatus();

  const runs = runsData?.items ?? [];

  const handleRefresh = () => {
    refetchPipeline();
    refetchRuns();
  };

  const handleTriggerRun = () => {
    triggerPipeline.mutate(pipelineId);
  };

  const handleToggleStatus = () => {
    if (!pipeline) return;
    const newStatus: PipelineStatus = pipeline.status === 'active' ? 'paused' : 'active';
    updateStatus.mutate({ pipelineId, status: newStatus });
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

  const getStatusIcon = (status: PipelineRunStatus | string) => {
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

  const formatSchedule = (cron: string | null) => {
    if (!cron) return 'No schedule';
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

  // Stats computed from runs data
  const successfulRuns = runs.filter((r) => r.status === 'completed').length;
  const runsWithDuration = runs.filter((r) => r.duration_seconds !== null);
  const avgDuration = runsWithDuration.length > 0
    ? Math.round(runsWithDuration.reduce((acc, r) => acc + (r.duration_seconds || 0), 0) / runsWithDuration.length)
    : 0;

  const isLoading = isPipelineLoading || isRunsLoading;
  const isRefetching = isPipelineRefetching || isRunsRefetching;

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading pipeline...</p>
        </div>
      </div>
    );
  }

  if (isPipelineError || !pipeline) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-center">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm font-medium">Failed to load pipeline</p>
          <p className="text-sm text-muted-foreground">
            {pipelineError instanceof Error ? pipelineError.message : 'Unknown error'}
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetchPipeline()}>
              Try Again
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/admin/pipelines">Back to Pipelines</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Generate pipeline code based on config
  const pipelineCode = `# Pipeline: ${pipeline.name}
# Description: ${pipeline.description}

from openforge.pipeline import Pipeline, Stage
from openforge.connectors import PostgreSQL, Snowflake

@Pipeline(
    name="${pipeline.name}",
    schedule="${pipeline.config.schedule || 'None'}",
    timeout=${pipeline.config.timeout_minutes * 60},
    retries=${pipeline.config.max_retries}
)
def data_sync_pipeline():
    source = PostgreSQL(os.environ["SOURCE_DB"])
    target = Snowflake(os.environ["TARGET_WAREHOUSE"])

    @Stage("Extract")
    def extract():
        return source.query("""
            SELECT * FROM production.orders
            WHERE updated_at > :last_run_time
        """)

    @Stage("Transform")
    def transform(data):
        return data.transform([
            normalize_timestamps,
            validate_schema,
            deduplicate_records
        ])

    @Stage("Load")
    def load(data):
        target.upsert(
            table="analytics.orders",
            data=data,
            key="order_id"
        )

    return extract() >> transform() >> load()
`;

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
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">{pipeline.name}</h1>
              <div
                className={cn(
                  'h-3 w-3 rounded-full',
                  getStatusColor(pipeline.status)
                )}
              />
            </div>
            <p className="text-muted-foreground">{pipeline.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefetching}
          >
            <RefreshCw
              className={cn('mr-2 h-4 w-4', isRefetching && 'animate-spin')}
            />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleStatus}
            disabled={updateStatus.isPending}
          >
            {pipeline.status === 'active' ? (
              <>
                <Pause className="mr-2 h-4 w-4" />
                Pause
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Resume
              </>
            )}
          </Button>
          <Button onClick={handleTriggerRun} disabled={triggerPipeline.isPending}>
            <Play className={cn('mr-2 h-4 w-4', triggerPipeline.isPending && 'animate-spin')} />
            Run Now
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{runs.length}</div>
            <p className="text-xs text-muted-foreground">Total Runs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">
              {runs.length > 0 ? ((successfulRuns / runs.length) * 100).toFixed(1) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">Success Rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{formatDuration(avgDuration)}</div>
            <p className="text-xs text-muted-foreground">Avg Duration</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-lg font-bold">{formatSchedule(pipeline.config.schedule)}</span>
            </div>
            <p className="text-xs text-muted-foreground">Schedule</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('runs')}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'runs'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <History className="mr-2 inline-block h-4 w-4" />
            Run History
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'config'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <Settings className="mr-2 inline-block h-4 w-4" />
            Configuration
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'code'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <Code className="mr-2 inline-block h-4 w-4" />
            Pipeline Code
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'runs' && (
        <div className="space-y-6">
          {/* Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Run Metrics</CardTitle>
              <CardDescription>
                Pipeline execution metrics over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <MetricsChart />
            </CardContent>
          </Card>

          {/* Run History */}
          <Card>
            <CardHeader>
              <CardTitle>Run History</CardTitle>
              <CardDescription>Recent pipeline executions</CardDescription>
            </CardHeader>
            <CardContent>
              {isRunsError ? (
                <div className="flex h-32 items-center justify-center text-muted-foreground">
                  Failed to load runs. <Button variant="link" onClick={() => refetchRuns()}>Try again</Button>
                </div>
              ) : runs.length === 0 ? (
                <div className="flex h-32 items-center justify-center text-muted-foreground">
                  No runs found for this pipeline
                </div>
              ) : (
                <div className="space-y-4">
                  {runs.map((run) => (
                    <div
                      key={run.id}
                      className="rounded-lg border p-4"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(run.status)}
                          <div>
                            <p className="font-medium">Run #{run.run_number}</p>
                            <p className="text-xs text-muted-foreground">
                              Triggered by {run.triggered_by}
                            </p>
                          </div>
                        </div>
                        <div className="text-right text-sm">
                          <p>{new Date(run.started_at).toLocaleString()}</p>
                          <p className="text-muted-foreground">
                            Duration: {formatDuration(run.duration_seconds)}
                          </p>
                        </div>
                      </div>

                      {/* Status badge */}
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
                            run.status === 'completed' && 'bg-green-500/10 text-green-600 border-green-500/30',
                            run.status === 'failed' && 'bg-red-500/10 text-red-600 border-red-500/30',
                            run.status === 'running' && 'bg-blue-500/10 text-blue-600 border-blue-500/30',
                            run.status === 'pending' && 'bg-yellow-500/10 text-yellow-600 border-yellow-500/30',
                            run.status === 'cancelled' && 'bg-gray-500/10 text-gray-600 border-gray-500/30'
                          )}
                        >
                          {run.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'config' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Schedule & Execution</CardTitle>
                <Button variant="ghost" size="sm">
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Schedule (cron)</span>
                  <code className="text-sm">{pipeline.config.schedule || 'None'}</code>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Timeout</span>
                  <span>{pipeline.config.timeout_minutes} minutes</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Max Retries</span>
                  <span>{pipeline.config.max_retries}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Concurrency</span>
                  <span>{pipeline.config.concurrency}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Pipeline Stages</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {pipeline.stages.length === 0 ? (
                <div className="flex h-20 items-center justify-center text-muted-foreground">
                  No stages configured
                </div>
              ) : (
                <div className="space-y-2">
                  {pipeline.stages.map((stage, index) => (
                    <div key={stage.id} className="flex items-center gap-3 border-b pb-2 last:border-0">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium">
                        {index + 1}
                      </span>
                      <div>
                        <p className="font-medium">{stage.name}</p>
                        <p className="text-xs text-muted-foreground">{stage.type}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Pipeline Info</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Created</span>
                  <span>{new Date(pipeline.created_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Updated</span>
                  <span>{new Date(pipeline.updated_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Last Run</span>
                  <span>{pipeline.last_run ? new Date(pipeline.last_run).toLocaleString() : 'Never'}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Next Run</span>
                  <span>{pipeline.next_run ? new Date(pipeline.next_run).toLocaleString() : 'Not scheduled'}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'code' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Pipeline Definition</CardTitle>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  <Copy className="mr-2 h-4 w-4" />
                  Copy
                </Button>
                <Button variant="outline" size="sm">
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="rounded-lg bg-muted p-4 overflow-x-auto">
              <code className="text-sm">{pipelineCode}</code>
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Danger Zone */}
      <Card className="border-red-500/50">
        <CardHeader>
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
          <CardDescription>
            Irreversible actions for this pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Delete Pipeline</p>
              <p className="text-sm text-muted-foreground">
                Permanently delete this pipeline and all its run history
              </p>
            </div>
            <Button variant="destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Pipeline
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
