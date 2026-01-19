'use client';

import * as React from 'react';
import {
  Clock,
  Check,
  X,
  MessageSquare,
  ArrowUp,
  AlertTriangle,
  User,
  Bot,
} from 'lucide-react';

import { cn, formatDateTime, formatRelativeTime } from '@/lib/utils';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { getInitials } from '@/lib/utils';

// Timeline event types
export type TimelineEventType =
  | 'created'
  | 'approved'
  | 'rejected'
  | 'changes_requested'
  | 'escalated'
  | 'expired'
  | 'comment'
  | 'updated';

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  actor: string;
  actor_type: 'user' | 'agent' | 'system';
  timestamp: string;
  message?: string;
  metadata?: Record<string, unknown>;
}

interface ApprovalTimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export function ApprovalTimeline({ events, className }: ApprovalTimelineProps) {
  // Sort events by timestamp (newest first for display, oldest first for the timeline)
  const sortedEvents = [...events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className={cn('relative', className)}>
      {/* Timeline line */}
      <div
        className="absolute left-4 top-0 bottom-0 w-px bg-border"
        aria-hidden="true"
      />

      <div className="space-y-6">
        {sortedEvents.map((event, index) => (
          <TimelineItem
            key={event.id}
            event={event}
            isLast={index === sortedEvents.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

interface TimelineItemProps {
  event: TimelineEvent;
  isLast: boolean;
}

function TimelineItem({ event, isLast }: TimelineItemProps) {
  const { icon: Icon, iconBgColor, iconColor } = getEventStyles(event.type);
  const ActorIcon = event.actor_type === 'agent' ? Bot : User;

  return (
    <div className="relative flex gap-4">
      {/* Icon */}
      <div
        className={cn(
          'relative z-10 flex h-8 w-8 items-center justify-center rounded-full',
          iconBgColor
        )}
      >
        <Icon className={cn('h-4 w-4', iconColor)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Avatar className="h-5 w-5">
              <AvatarFallback className="text-[10px]">
                {event.actor_type === 'system' ? (
                  <Bot className="h-3 w-3" />
                ) : (
                  getInitials(event.actor)
                )}
              </AvatarFallback>
            </Avatar>
            <span className="font-medium text-sm truncate">
              {event.actor_type === 'system' ? 'System' : event.actor}
            </span>
            <span className="text-sm text-muted-foreground">
              {getEventLabel(event.type)}
            </span>
          </div>
          <time
            className="text-xs text-muted-foreground flex-shrink-0"
            dateTime={event.timestamp}
            title={formatDateTime(event.timestamp)}
          >
            {formatRelativeTime(event.timestamp)}
          </time>
        </div>

        {event.message && (
          <div className="mt-2 rounded-lg bg-muted/50 p-3 text-sm">
            {event.message}
          </div>
        )}

        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="mt-2 text-xs text-muted-foreground">
            {formatMetadata(event.metadata)}
          </div>
        )}
      </div>
    </div>
  );
}

function getEventStyles(type: TimelineEventType): {
  icon: React.ComponentType<{ className?: string }>;
  iconBgColor: string;
  iconColor: string;
} {
  switch (type) {
    case 'created':
      return {
        icon: Clock,
        iconBgColor: 'bg-blue-100 dark:bg-blue-900/30',
        iconColor: 'text-blue-600 dark:text-blue-400',
      };
    case 'approved':
      return {
        icon: Check,
        iconBgColor: 'bg-green-100 dark:bg-green-900/30',
        iconColor: 'text-green-600 dark:text-green-400',
      };
    case 'rejected':
      return {
        icon: X,
        iconBgColor: 'bg-red-100 dark:bg-red-900/30',
        iconColor: 'text-red-600 dark:text-red-400',
      };
    case 'changes_requested':
      return {
        icon: MessageSquare,
        iconBgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
        iconColor: 'text-yellow-600 dark:text-yellow-400',
      };
    case 'escalated':
      return {
        icon: ArrowUp,
        iconBgColor: 'bg-orange-100 dark:bg-orange-900/30',
        iconColor: 'text-orange-600 dark:text-orange-400',
      };
    case 'expired':
      return {
        icon: AlertTriangle,
        iconBgColor: 'bg-gray-100 dark:bg-gray-900/30',
        iconColor: 'text-gray-600 dark:text-gray-400',
      };
    case 'comment':
      return {
        icon: MessageSquare,
        iconBgColor: 'bg-muted',
        iconColor: 'text-muted-foreground',
      };
    case 'updated':
    default:
      return {
        icon: Clock,
        iconBgColor: 'bg-muted',
        iconColor: 'text-muted-foreground',
      };
  }
}

function getEventLabel(type: TimelineEventType): string {
  switch (type) {
    case 'created':
      return 'created this request';
    case 'approved':
      return 'approved this request';
    case 'rejected':
      return 'rejected this request';
    case 'changes_requested':
      return 'requested changes';
    case 'escalated':
      return 'escalated this request';
    case 'expired':
      return 'marked as expired';
    case 'comment':
      return 'commented';
    case 'updated':
      return 'updated this request';
    default:
      return 'performed an action';
  }
}

function formatMetadata(metadata: Record<string, unknown>): string {
  const parts: string[] = [];

  if (metadata.previous_level && metadata.new_level) {
    parts.push(`Escalated from ${metadata.previous_level} to ${metadata.new_level}`);
  }

  if (metadata.reason) {
    parts.push(`Reason: ${metadata.reason}`);
  }

  return parts.join(' - ');
}

// Export a compact version for inline use
export function ApprovalTimelineCompact({
  events,
  maxEvents = 3,
  className,
}: {
  events: TimelineEvent[];
  maxEvents?: number;
  className?: string;
}) {
  const recentEvents = [...events]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, maxEvents);

  return (
    <div className={cn('space-y-2', className)}>
      {recentEvents.map((event) => {
        const { icon: Icon, iconColor } = getEventStyles(event.type);
        return (
          <div key={event.id} className="flex items-center gap-2 text-sm">
            <Icon className={cn('h-3 w-3', iconColor)} />
            <span className="text-muted-foreground truncate">
              {event.actor} {getEventLabel(event.type)}
            </span>
            <span className="text-xs text-muted-foreground flex-shrink-0">
              {formatRelativeTime(event.timestamp)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
