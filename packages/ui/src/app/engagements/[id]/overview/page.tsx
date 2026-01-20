'use client';

import { Suspense, use } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  PhaseProgress,
  ActivityFeed,
  ActivityFeedSkeleton,
  StatusBadge,
} from '@/components/engagements';
import type { ActivityItem } from '@/components/engagements';
import { useEngagement } from '@/lib/hooks/use-engagement';
import { useAgentTasks } from '@/lib/hooks/use-agent';
import { useApprovals } from '@/lib/hooks/use-approval';
import { formatDate, formatDateTime, formatRelativeTime } from '@/lib/utils';
import {
  Calendar,
  Clock,
  Database,
  Flag,
  Loader2,
  Tag,
  User,
} from 'lucide-react';

const priorityColors: Record<string, string> = {
  low: 'text-slate-500',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  critical: 'text-red-500',
};

// TODO: Activities endpoint doesn't exist yet - replace with real API when available
const mockActivities: ActivityItem[] = [];

interface OverviewPageProps {
  params: Promise<{ id: string }>;
}

export default function OverviewPage({ params }: OverviewPageProps) {
  const { id } = use(params);
  const { data: engagement, isLoading: engLoading, error: engError } = useEngagement(id);
  const { data: tasksData, isLoading: tasksLoading } = useAgentTasks(id);
  const { data: approvalsData, isLoading: approvalsLoading } = useApprovals({ pending_only: true });

  if (engLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (engError || !engagement) {
    return (
      <Card className="flex flex-col items-center justify-center py-12 text-center">
        <h3 className="text-lg font-medium">Error loading engagement</h3>
        <p className="text-sm text-muted-foreground">
          {engError?.message || 'Engagement not found'}
        </p>
      </Card>
    );
  }

  const tasks = tasksData?.items ?? [];
  const runningTasks = tasks.filter((t) => t.status === 'running').length;
  const completedTasks = tasks.filter((t) => t.status === 'completed').length;
  const pendingApprovals = approvalsData?.items?.length ?? 0;

  // Calculate runtime if started
  let runtimeDisplay = '-';
  if (engagement.started_at) {
    const startTime = new Date(engagement.started_at).getTime();
    const endTime = engagement.completed_at
      ? new Date(engagement.completed_at).getTime()
      : Date.now();
    const diffMs = endTime - startTime;
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    runtimeDisplay = `${hours}h ${minutes}m`;
  }

  return (
    <div className="space-y-6">
      {/* Phase Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Progress</CardTitle>
          <CardDescription>
            Current phase and completion status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PhaseProgress status={engagement.status} currentPhase={3} />
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Engagement Details */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Objective */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-muted-foreground">Objective</h4>
              <p>{engagement.objective}</p>
            </div>

            {/* Metadata Grid */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                  <User className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Created By</p>
                  <p className="text-sm font-medium">{engagement.created_by}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                  <Flag className={`h-4 w-4 ${priorityColors[engagement.priority]}`} />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Priority</p>
                  <p className="text-sm font-medium capitalize">{engagement.priority}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Created</p>
                  <p className="text-sm font-medium">
                    {formatDate(engagement.created_at)}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Last Updated</p>
                  <p className="text-sm font-medium">
                    {formatRelativeTime(engagement.updated_at)}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                  <Database className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Data Sources</p>
                  <p className="text-sm font-medium">
                    {engagement.data_sources.length} connected
                  </p>
                </div>
              </div>

              {engagement.started_at && (
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Started</p>
                    <p className="text-sm font-medium">
                      {formatDateTime(engagement.started_at)}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Tags */}
            {engagement.tags.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Tags</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {engagement.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-secondary text-secondary-foreground text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Activity Feed */}
        <Card>
          <CardHeader>
            <CardTitle>Activity</CardTitle>
            <CardDescription>Recent events</CardDescription>
          </CardHeader>
          <CardContent>
            <Suspense fallback={<ActivityFeedSkeleton count={5} />}>
              {/* TODO: Replace mockActivities with real activity data when API is available */}
              <ActivityFeed
                activities={mockActivities}
                maxItems={5}
              />
            </Suspense>
          </CardContent>
        </Card>
      </div>

      {/* Statistics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Runtime"
          value={runtimeDisplay}
          description="Since started"
        />
        <StatCard
          title="Data Sources"
          value={String(engagement.data_sources.length)}
          description="Connected sources"
        />
        <StatCard
          title="Agent Tasks"
          value={tasksLoading ? '-' : String(tasks.length)}
          description={tasksLoading ? 'Loading...' : `${runningTasks} running, ${completedTasks} completed`}
        />
        <StatCard
          title="Pending Approvals"
          value={approvalsLoading ? '-' : String(pendingApprovals)}
          description="Waiting for review"
        />
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string;
  description: string;
}

function StatCard({ title, value, description }: StatCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}
