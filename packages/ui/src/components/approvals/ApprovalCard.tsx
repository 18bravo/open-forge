'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Bot,
  Database,
  Settings,
  Rocket,
  Key,
  Users,
  Terminal,
  Eye,
  Table,
  FileQuestion,
  Clock,
  AlertTriangle,
  ArrowUpRight,
} from 'lucide-react';

import { cn, formatRelativeTime } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  ApprovalListItem,
  ApprovalType,
  ApprovalStatus,
  getApprovalStatusColor,
  getApprovalTypeLabel,
  isUrgent,
  isExpiringSoon,
  EscalationLevel,
} from '@/types/approvals';

// Icon mapping
const typeIcons: Record<ApprovalType, React.ComponentType<{ className?: string }>> = {
  [ApprovalType.AGENT_ACTION]: Bot,
  [ApprovalType.DATA_CHANGE]: Database,
  [ApprovalType.CONFIGURATION]: Settings,
  [ApprovalType.DEPLOYMENT]: Rocket,
  [ApprovalType.ACCESS_GRANT]: Key,
  [ApprovalType.ENGAGEMENT]: Users,
  [ApprovalType.TOOL_EXECUTION]: Terminal,
  [ApprovalType.DATA_ACCESS]: Eye,
  [ApprovalType.SCHEMA_CHANGE]: Table,
};

interface ApprovalCardProps {
  approval: ApprovalListItem;
  selected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  showCheckbox?: boolean;
  className?: string;
}

export function ApprovalCard({
  approval,
  selected = false,
  onSelect,
  showCheckbox = false,
  className,
}: ApprovalCardProps) {
  const Icon = typeIcons[approval.approval_type] || FileQuestion;
  const urgent = isUrgent(approval);
  const expiringSoon = isExpiringSoon(approval);
  const isEscalated = approval.escalation_level !== 'level_1';

  return (
    <Card
      className={cn(
        'transition-all hover:shadow-md',
        urgent && 'border-red-500 dark:border-red-500',
        expiringSoon && !urgent && 'border-yellow-500 dark:border-yellow-500',
        selected && 'ring-2 ring-primary',
        className
      )}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Checkbox for bulk selection */}
          {showCheckbox && (
            <Checkbox
              checked={selected}
              onCheckedChange={(checked) => onSelect?.(approval.id, !!checked)}
              className="mt-1"
              aria-label={`Select approval ${approval.title}`}
            />
          )}

          {/* Type Icon */}
          <div
            className={cn(
              'flex-shrink-0 rounded-lg p-2',
              'bg-muted'
            )}
          >
            <Icon className="h-5 w-5 text-muted-foreground" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <Link
                  href={`/approvals/${approval.id}`}
                  className="group flex items-center gap-1"
                >
                  <h3 className="font-medium truncate group-hover:text-primary transition-colors">
                    {approval.title}
                  </h3>
                  <ArrowUpRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Requested by {approval.requested_by} {formatRelativeTime(approval.requested_at)}
                </p>
              </div>

              <Badge
                variant="secondary"
                className={cn('flex-shrink-0', getApprovalStatusColor(approval.status))}
              >
                {approval.status}
              </Badge>
            </div>

            {/* Tags and deadline */}
            <div className="flex items-center flex-wrap gap-2 mt-2">
              <Badge variant="outline" className="text-xs">
                {getApprovalTypeLabel(approval.approval_type)}
              </Badge>

              {isEscalated && (
                <Badge variant="outline" className="text-xs bg-orange-50 dark:bg-orange-900/20">
                  Escalated: {formatEscalationLevel(approval.escalation_level)}
                </Badge>
              )}

              {urgent && (
                <Badge variant="destructive" className="text-xs flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Urgent
                </Badge>
              )}

              {approval.deadline && (
                <span
                  className={cn(
                    'text-xs flex items-center gap-1',
                    urgent
                      ? 'text-red-600 dark:text-red-400'
                      : expiringSoon
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-muted-foreground'
                  )}
                >
                  <Clock className="h-3 w-3" />
                  Due {formatRelativeTime(approval.deadline)}
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function formatEscalationLevel(level: EscalationLevel): string {
  switch (level) {
    case 'level_1':
      return 'L1';
    case 'level_2':
      return 'L2';
    case 'level_3':
      return 'L3';
    case 'executive':
      return 'Exec';
    default:
      return level;
  }
}

// Export compact version for dense lists
export function ApprovalCardCompact({
  approval,
  className,
}: {
  approval: ApprovalListItem;
  className?: string;
}) {
  const Icon = typeIcons[approval.approval_type] || FileQuestion;
  const urgent = isUrgent(approval);

  return (
    <Link
      href={`/approvals/${approval.id}`}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border transition-colors',
        'hover:bg-muted/50',
        urgent && 'border-red-500',
        className
      )}
    >
      <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <span className="flex-1 truncate text-sm font-medium">{approval.title}</span>
      <Badge
        variant="secondary"
        className={cn('text-xs', getApprovalStatusColor(approval.status))}
      >
        {approval.status}
      </Badge>
    </Link>
  );
}
