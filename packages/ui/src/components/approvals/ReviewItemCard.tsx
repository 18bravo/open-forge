'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  BarChart3,
  Bot,
  Settings,
  GitMerge,
  AlertTriangle,
  Shield,
  FileQuestion,
  Clock,
  User,
  ArrowUpRight,
} from 'lucide-react';

import { cn, formatRelativeTime } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Checkbox } from '@/components/ui/checkbox';
import { getInitials } from '@/lib/utils';
import {
  ReviewListItem,
  ReviewCategory,
  ReviewStatus,
  ReviewPriority,
  getReviewStatusColor,
  getPriorityColor,
  getPriorityLabel,
  getReviewCategoryLabel,
} from '@/types/reviews';

// Icon mapping
const categoryIcons: Record<ReviewCategory, React.ComponentType<{ className?: string }>> = {
  [ReviewCategory.DATA_QUALITY]: BarChart3,
  [ReviewCategory.AGENT_OUTPUT]: Bot,
  [ReviewCategory.CONFIGURATION]: Settings,
  [ReviewCategory.MAPPING]: GitMerge,
  [ReviewCategory.ANOMALY]: AlertTriangle,
  [ReviewCategory.COMPLIANCE]: Shield,
};

interface ReviewItemCardProps {
  item: ReviewListItem;
  selected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  showCheckbox?: boolean;
  className?: string;
}

export function ReviewItemCard({
  item,
  selected = false,
  onSelect,
  showCheckbox = false,
  className,
}: ReviewItemCardProps) {
  const Icon = categoryIcons[item.category] || FileQuestion;
  const isCritical = item.priority === ReviewPriority.CRITICAL;
  const isHigh = item.priority === ReviewPriority.HIGH;

  return (
    <Card
      className={cn(
        'transition-all hover:shadow-md',
        isCritical && 'border-red-500 dark:border-red-500',
        isHigh && !isCritical && 'border-orange-500 dark:border-orange-500',
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
              onCheckedChange={(checked) => onSelect?.(item.id, !!checked)}
              className="mt-1"
              aria-label={`Select review item ${item.title}`}
            />
          )}

          {/* Category Icon */}
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
                  href={`/reviews/${item.id}`}
                  className="group flex items-center gap-1"
                >
                  <h3 className="font-medium truncate group-hover:text-primary transition-colors">
                    {item.title}
                  </h3>
                  <ArrowUpRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
                <p className="text-sm text-muted-foreground mt-0.5 flex items-center gap-2">
                  <Clock className="h-3 w-3" />
                  Created {formatRelativeTime(item.created_at)}
                </p>
              </div>

              <div className="flex flex-col items-end gap-1">
                <Badge
                  variant="secondary"
                  className={cn('flex-shrink-0', getReviewStatusColor(item.status))}
                >
                  {item.status.replace('_', ' ')}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn('text-xs', getPriorityColor(item.priority))}
                >
                  {getPriorityLabel(item.priority)}
                </Badge>
              </div>
            </div>

            {/* Tags and assignee */}
            <div className="flex items-center flex-wrap gap-2 mt-2">
              <Badge variant="outline" className="text-xs">
                {getReviewCategoryLabel(item.category)}
              </Badge>

              {item.batch_id && (
                <Badge variant="outline" className="text-xs bg-purple-50 dark:bg-purple-900/20">
                  Batch
                </Badge>
              )}

              {item.assigned_to && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Avatar className="h-4 w-4">
                    <AvatarFallback className="text-[8px]">
                      {getInitials(item.assigned_to)}
                    </AvatarFallback>
                  </Avatar>
                  <span>{item.assigned_to}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Compact version for dense lists
export function ReviewItemCardCompact({
  item,
  className,
}: {
  item: ReviewListItem;
  className?: string;
}) {
  const Icon = categoryIcons[item.category] || FileQuestion;
  const isCritical = item.priority === ReviewPriority.CRITICAL;

  return (
    <Link
      href={`/reviews/${item.id}`}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border transition-colors',
        'hover:bg-muted/50',
        isCritical && 'border-red-500',
        className
      )}
    >
      <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <span className="flex-1 truncate text-sm font-medium">{item.title}</span>
      <Badge
        variant="outline"
        className={cn('text-xs', getPriorityColor(item.priority))}
      >
        {getPriorityLabel(item.priority)}
      </Badge>
      <Badge
        variant="secondary"
        className={cn('text-xs', getReviewStatusColor(item.status))}
      >
        {item.status.replace('_', ' ')}
      </Badge>
    </Link>
  );
}

// List view for review items
export function ReviewItemList({
  items,
  selectedIds,
  onSelectItem,
  showCheckbox = false,
  emptyMessage = 'No review items',
  className,
}: {
  items: ReviewListItem[];
  selectedIds?: Set<string>;
  onSelectItem?: (id: string, selected: boolean) => void;
  showCheckbox?: boolean;
  emptyMessage?: string;
  className?: string;
}) {
  if (items.length === 0) {
    return (
      <div className={cn('text-center py-8 text-muted-foreground', className)}>
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {items.map((item) => (
        <ReviewItemCard
          key={item.id}
          item={item}
          selected={selectedIds?.has(item.id)}
          onSelect={onSelectItem}
          showCheckbox={showCheckbox}
        />
      ))}
    </div>
  );
}
