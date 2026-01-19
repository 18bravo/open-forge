import { cn } from '@/lib/utils';
import type { EngagementStatus, ApprovalStatus, AgentTaskStatus } from '@/lib/api';

type Status = EngagementStatus | ApprovalStatus | AgentTaskStatus;

interface StatusBadgeProps {
  status: Status;
  className?: string;
  size?: 'sm' | 'default' | 'lg';
}

const statusConfig: Record<
  Status,
  { label: string; className: string }
> = {
  // Engagement statuses
  draft: {
    label: 'Draft',
    className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  },
  pending_approval: {
    label: 'Pending Approval',
    className: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  },
  approved: {
    label: 'Approved',
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  },
  in_progress: {
    label: 'In Progress',
    className: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-300',
  },
  paused: {
    label: 'Paused',
    className: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  },
  // Approval statuses
  pending: {
    label: 'Pending',
    className: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  },
  rejected: {
    label: 'Rejected',
    className: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  },
  expired: {
    label: 'Expired',
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  },
  // Agent task statuses
  queued: {
    label: 'Queued',
    className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  },
  running: {
    label: 'Running',
    className: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-300',
  },
  waiting_approval: {
    label: 'Waiting Approval',
    className: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  },
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  default: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

export function StatusBadge({ status, className, size = 'default' }: StatusBadgeProps) {
  const config = statusConfig[status];

  if (!config) {
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-full font-medium',
          'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
          sizeClasses[size],
          className
        )}
      >
        {status}
      </span>
    );
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        config.className,
        sizeClasses[size],
        className
      )}
    >
      {config.label}
    </span>
  );
}
