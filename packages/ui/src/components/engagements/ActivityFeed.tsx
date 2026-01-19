'use client';

import * as React from 'react';
import { cn, formatRelativeTime } from '@/lib/utils';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  MessageSquare,
  Play,
  Settings,
  User,
  XCircle,
} from 'lucide-react';

export interface ActivityItem {
  id: string;
  type:
    | 'engagement_created'
    | 'engagement_started'
    | 'engagement_completed'
    | 'engagement_failed'
    | 'approval_requested'
    | 'approval_granted'
    | 'approval_rejected'
    | 'data_source_added'
    | 'data_source_connected'
    | 'agent_task_started'
    | 'agent_task_completed'
    | 'agent_message'
    | 'ontology_updated'
    | 'config_changed';
  title: string;
  description?: string;
  timestamp: string;
  user?: string;
  metadata?: Record<string, unknown>;
}

const activityIcons: Record<ActivityItem['type'], React.ReactNode> = {
  engagement_created: <FileText className="h-4 w-4" />,
  engagement_started: <Play className="h-4 w-4" />,
  engagement_completed: <CheckCircle2 className="h-4 w-4" />,
  engagement_failed: <XCircle className="h-4 w-4" />,
  approval_requested: <Clock className="h-4 w-4" />,
  approval_granted: <CheckCircle2 className="h-4 w-4" />,
  approval_rejected: <XCircle className="h-4 w-4" />,
  data_source_added: <Database className="h-4 w-4" />,
  data_source_connected: <Database className="h-4 w-4" />,
  agent_task_started: <Activity className="h-4 w-4" />,
  agent_task_completed: <CheckCircle2 className="h-4 w-4" />,
  agent_message: <MessageSquare className="h-4 w-4" />,
  ontology_updated: <Settings className="h-4 w-4" />,
  config_changed: <Settings className="h-4 w-4" />,
};

const activityColors: Record<ActivityItem['type'], string> = {
  engagement_created: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
  engagement_started: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900 dark:text-cyan-400',
  engagement_completed: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
  engagement_failed: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
  approval_requested: 'bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-400',
  approval_granted: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
  approval_rejected: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
  data_source_added: 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
  data_source_connected: 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
  agent_task_started: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900 dark:text-cyan-400',
  agent_task_completed: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
  agent_message: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
  ontology_updated: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400',
  config_changed: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
};

interface ActivityFeedProps {
  activities: ActivityItem[];
  className?: string;
  showTimeline?: boolean;
  maxItems?: number;
  emptyMessage?: string;
}

export function ActivityFeed({
  activities,
  className,
  showTimeline = true,
  maxItems,
  emptyMessage = 'No activity yet',
}: ActivityFeedProps) {
  const displayedActivities = maxItems ? activities.slice(0, maxItems) : activities;

  if (displayedActivities.length === 0) {
    return (
      <div className={cn('flex flex-col items-center justify-center py-8 text-center', className)}>
        <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {displayedActivities.map((activity, index) => (
        <div key={activity.id} className="flex gap-3">
          {showTimeline && (
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full',
                  activityColors[activity.type]
                )}
              >
                {activityIcons[activity.type]}
              </div>
              {index < displayedActivities.length - 1 && (
                <div className="w-px flex-1 bg-border mt-2" />
              )}
            </div>
          )}
          <div className="flex-1 pt-1 pb-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-medium leading-tight">{activity.title}</p>
                {activity.description && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {activity.description}
                  </p>
                )}
              </div>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {formatRelativeTime(activity.timestamp)}
              </span>
            </div>
            {activity.user && (
              <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                <User className="h-3 w-3" />
                <span>{activity.user}</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function ActivityFeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex gap-3 animate-pulse">
          <div className="h-8 w-8 rounded-full bg-muted" />
          <div className="flex-1 space-y-2 pt-1">
            <div className="h-4 w-3/4 bg-muted rounded" />
            <div className="h-3 w-1/2 bg-muted rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}
