'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { StatusBadge } from './StatusBadge';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { EngagementSummary, EngagementPriority } from '@/lib/api';
import {
  AlertTriangle,
  ArrowRight,
  Clock,
  Flag,
  User,
} from 'lucide-react';

interface EngagementCardProps {
  engagement: EngagementSummary;
  className?: string;
}

const priorityConfig: Record<
  EngagementPriority,
  { icon: React.ReactNode; className: string }
> = {
  low: {
    icon: <Flag className="h-3.5 w-3.5" />,
    className: 'text-slate-500',
  },
  medium: {
    icon: <Flag className="h-3.5 w-3.5" />,
    className: 'text-blue-500',
  },
  high: {
    icon: <Flag className="h-3.5 w-3.5 fill-current" />,
    className: 'text-orange-500',
  },
  critical: {
    icon: <AlertTriangle className="h-3.5 w-3.5 fill-current" />,
    className: 'text-red-500',
  },
};

export function EngagementCard({ engagement, className }: EngagementCardProps) {
  const priority = priorityConfig[engagement.priority];

  return (
    <Link href={`/engagements/${engagement.id}`}>
      <Card
        className={cn(
          'group relative overflow-hidden transition-all hover:shadow-md hover:border-primary/50',
          className
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1 flex-1 min-w-0">
              <CardTitle className="text-lg truncate group-hover:text-primary transition-colors">
                {engagement.name}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 text-xs">
                <User className="h-3 w-3" />
                <span className="truncate">{engagement.created_by}</span>
              </CardDescription>
            </div>
            <StatusBadge status={engagement.status} size="sm" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <div className={cn('flex items-center gap-1', priority.className)}>
                {priority.icon}
                <span className="capitalize text-xs">{engagement.priority}</span>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                <span className="text-xs">
                  {formatRelativeTime(engagement.updated_at)}
                </span>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

interface EngagementCardSkeletonProps {
  className?: string;
}

export function EngagementCardSkeleton({ className }: EngagementCardSkeletonProps) {
  return (
    <Card className={cn('animate-pulse', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-2 flex-1">
            <div className="h-5 bg-muted rounded w-3/4" />
            <div className="h-3 bg-muted rounded w-1/2" />
          </div>
          <div className="h-5 w-20 bg-muted rounded-full" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="h-4 w-16 bg-muted rounded" />
          <div className="h-4 w-20 bg-muted rounded" />
        </div>
      </CardContent>
    </Card>
  );
}
