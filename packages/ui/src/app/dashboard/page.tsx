'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  EngagementCard,
  EngagementCardSkeleton,
  ActivityFeed,
  ActivityFeedSkeleton,
} from '@/components/engagements';
import type { EngagementSummary } from '@/lib/api';
import { useEngagements, useRecentActivities, useDashboardMetrics } from '@/lib/hooks';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity,
  ArrowRight,
  CheckCircle,
  Clock,
  Database,
  FileText,
  Plus,
  AlertTriangle,
} from 'lucide-react';

export default function DashboardPage() {
  // Fetch data from API
  const { data: engagementsData, isLoading: engagementsLoading } = useEngagements({ page_size: 3 });
  const { data: activitiesData, isLoading: activitiesLoading } = useRecentActivities(5);
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics();

  const engagements = engagementsData?.items ?? [];
  const activities = activitiesData?.items ?? [];
  const dashboardMetrics = metrics ?? {
    activeEngagements: 0,
    pendingApprovals: 0,
    dataSources: 0,
    completedThisMonth: 0,
  };
  return (
    <div className="container py-6 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here is an overview of your engagements.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href="/engagements">
              View All Engagements
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button asChild>
            <Link href="/engagements/new">
              <Plus className="mr-2 h-4 w-4" />
              New Engagement
            </Link>
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricsLoading ? (
          <>
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
          </>
        ) : (
          <>
            <MetricCard
              title="Active Engagements"
              value={dashboardMetrics.activeEngagements}
              description="Currently running"
              icon={<Activity className="h-4 w-4 text-cyan-500" />}
              href="/engagements?status=in_progress"
            />
            <MetricCard
              title="Pending Approvals"
              value={dashboardMetrics.pendingApprovals}
              description="Awaiting your review"
              icon={<Clock className="h-4 w-4 text-amber-500" />}
              href="/approvals?status=pending"
              highlight={dashboardMetrics.pendingApprovals > 0}
            />
            <MetricCard
              title="Data Sources"
              value={dashboardMetrics.dataSources}
              description="Connected sources"
              icon={<Database className="h-4 w-4 text-purple-500" />}
              href="/data-sources"
            />
            <MetricCard
              title="Completed This Month"
              value={dashboardMetrics.completedThisMonth}
              description="Successful engagements"
              icon={<CheckCircle className="h-4 w-4 text-green-500" />}
              href="/engagements?status=completed"
            />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Active Engagements */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Active Engagements</h2>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/engagements">
                View all
                <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          </div>
          {engagementsLoading ? (
            <EngagementListSkeleton />
          ) : (
            <EngagementList engagements={engagements} />
          )}
        </div>

        {/* Activity Feed */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Recent Activity</h2>
          <Card>
            <CardContent className="pt-6">
              {activitiesLoading ? (
                <ActivityFeedSkeleton count={4} />
              ) : (
                <ActivityFeed activities={activities} maxItems={5} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <QuickActionCard
            title="New Engagement"
            description="Start a new data engagement"
            icon={<Plus className="h-5 w-5" />}
            href="/engagements/new"
          />
          <QuickActionCard
            title="Add Data Source"
            description="Connect a new data source"
            icon={<Database className="h-5 w-5" />}
            href="/data-sources/new"
          />
          <QuickActionCard
            title="Review Approvals"
            description="Pending approval requests"
            icon={<FileText className="h-5 w-5" />}
            href="/approvals"
            badge={dashboardMetrics.pendingApprovals > 0 ? dashboardMetrics.pendingApprovals : undefined}
          />
          <QuickActionCard
            title="View Reports"
            description="Analytics and insights"
            icon={<Activity className="h-5 w-5" />}
            href="/reports"
          />
        </div>
      </div>
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: number;
  description: string;
  icon: React.ReactNode;
  href: string;
  highlight?: boolean;
}

function MetricCard({ title, value, description, icon, href, highlight }: MetricCardProps) {
  return (
    <Link href={href}>
      <Card className={`transition-all hover:shadow-md hover:border-primary/50 ${highlight ? 'border-amber-500/50' : ''}`}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {icon}
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">{description}</p>
        </CardContent>
      </Card>
    </Link>
  );
}

// Quick Action Card Component
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

function QuickActionCard({ title, description, icon, href, badge }: QuickActionCardProps) {
  return (
    <Link href={href}>
      <Card className="group relative transition-all hover:shadow-md hover:border-primary/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              {icon}
            </div>
            <div>
              <CardTitle className="text-base">{title}</CardTitle>
              <CardDescription className="text-xs">{description}</CardDescription>
            </div>
          </div>
        </CardHeader>
        {badge && (
          <div className="absolute top-3 right-3">
            <span className="inline-flex items-center justify-center h-5 w-5 text-xs font-medium bg-amber-500 text-white rounded-full">
              {badge}
            </span>
          </div>
        )}
      </Card>
    </Link>
  );
}

// Engagement List Component
function EngagementList({ engagements }: { engagements: EngagementSummary[] }) {
  if (engagements.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center py-12 text-center">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium">No active engagements</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Get started by creating your first engagement.
        </p>
        <Button asChild>
          <Link href="/engagements/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Engagement
          </Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {engagements.map((engagement) => (
        <EngagementCard key={engagement.id} engagement={engagement} />
      ))}
    </div>
  );
}

// Skeleton for engagement list
function EngagementListSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <EngagementCardSkeleton key={i} />
      ))}
    </div>
  );
}
