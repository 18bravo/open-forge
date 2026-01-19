'use client';

import * as React from 'react';
import { Plus, Minus, Equal } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';

interface DiffViewerProps {
  before: Record<string, unknown> | string | null;
  after: Record<string, unknown> | string | null;
  title?: string;
  maxHeight?: string;
  className?: string;
}

export function DiffViewer({
  before,
  after,
  title = 'Changes',
  maxHeight = '400px',
  className,
}: DiffViewerProps) {
  const [viewMode, setViewMode] = React.useState<'split' | 'unified'>('unified');

  // Convert to strings if objects
  const beforeStr = typeof before === 'string' ? before : JSON.stringify(before, null, 2);
  const afterStr = typeof after === 'string' ? after : JSON.stringify(after, null, 2);

  // Compute diff
  const diff = computeDiff(beforeStr, afterStr);

  return (
    <div className={cn('rounded-lg border', className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        <Tabs
          value={viewMode}
          onValueChange={(v) => setViewMode(v as 'split' | 'unified')}
          className="w-auto"
        >
          <TabsList className="h-7">
            <TabsTrigger value="unified" className="text-xs px-2 py-1">
              Unified
            </TabsTrigger>
            <TabsTrigger value="split" className="text-xs px-2 py-1">
              Split
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content */}
      <ScrollArea style={{ maxHeight }}>
        {viewMode === 'unified' ? (
          <UnifiedDiff diff={diff} />
        ) : (
          <SplitDiff before={beforeStr} after={afterStr} diff={diff} />
        )}
      </ScrollArea>

      {/* Summary */}
      <div className="flex items-center gap-4 border-t px-4 py-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
          <Plus className="h-3 w-3" />
          {diff.filter((d) => d.type === 'add').length} additions
        </span>
        <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
          <Minus className="h-3 w-3" />
          {diff.filter((d) => d.type === 'remove').length} deletions
        </span>
        <span className="flex items-center gap-1">
          <Equal className="h-3 w-3" />
          {diff.filter((d) => d.type === 'unchanged').length} unchanged
        </span>
      </div>
    </div>
  );
}

interface DiffLine {
  type: 'add' | 'remove' | 'unchanged';
  content: string;
  lineNumberBefore?: number;
  lineNumberAfter?: number;
}

function UnifiedDiff({ diff }: { diff: DiffLine[] }) {
  return (
    <div className="font-mono text-sm">
      {diff.map((line, index) => (
        <div
          key={index}
          className={cn(
            'flex px-4 py-0.5',
            line.type === 'add' && 'bg-green-50 dark:bg-green-900/20',
            line.type === 'remove' && 'bg-red-50 dark:bg-red-900/20'
          )}
        >
          <span className="w-12 flex-shrink-0 text-muted-foreground text-right pr-4 select-none">
            {line.lineNumberBefore ?? ''}
          </span>
          <span className="w-12 flex-shrink-0 text-muted-foreground text-right pr-4 select-none">
            {line.lineNumberAfter ?? ''}
          </span>
          <span
            className={cn(
              'w-4 flex-shrink-0 select-none',
              line.type === 'add' && 'text-green-600 dark:text-green-400',
              line.type === 'remove' && 'text-red-600 dark:text-red-400'
            )}
          >
            {line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' '}
          </span>
          <span
            className={cn(
              'flex-1 whitespace-pre-wrap break-all',
              line.type === 'add' && 'text-green-800 dark:text-green-300',
              line.type === 'remove' && 'text-red-800 dark:text-red-300'
            )}
          >
            {line.content}
          </span>
        </div>
      ))}
    </div>
  );
}

function SplitDiff({
  before,
  after,
  diff,
}: {
  before: string;
  after: string;
  diff: DiffLine[];
}) {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');

  // Create paired lines for split view
  const pairs: Array<{ before?: string; after?: string; beforeIdx?: number; afterIdx?: number }> = [];

  let beforeIdx = 0;
  let afterIdx = 0;

  for (const line of diff) {
    if (line.type === 'unchanged') {
      pairs.push({
        before: beforeLines[beforeIdx],
        after: afterLines[afterIdx],
        beforeIdx: beforeIdx + 1,
        afterIdx: afterIdx + 1,
      });
      beforeIdx++;
      afterIdx++;
    } else if (line.type === 'remove') {
      pairs.push({
        before: beforeLines[beforeIdx],
        beforeIdx: beforeIdx + 1,
      });
      beforeIdx++;
    } else if (line.type === 'add') {
      pairs.push({
        after: afterLines[afterIdx],
        afterIdx: afterIdx + 1,
      });
      afterIdx++;
    }
  }

  return (
    <div className="font-mono text-sm flex">
      {/* Before */}
      <div className="flex-1 border-r">
        <div className="px-2 py-1 text-xs font-medium text-muted-foreground bg-muted/50 border-b">
          Before
        </div>
        {pairs.map((pair, index) => (
          <div
            key={`before-${index}`}
            className={cn(
              'flex px-2 py-0.5',
              pair.before !== undefined && pair.after === undefined && 'bg-red-50 dark:bg-red-900/20'
            )}
          >
            <span className="w-8 flex-shrink-0 text-muted-foreground text-right pr-2 select-none">
              {pair.beforeIdx ?? ''}
            </span>
            <span
              className={cn(
                'flex-1 whitespace-pre-wrap break-all',
                pair.before !== undefined && pair.after === undefined && 'text-red-800 dark:text-red-300'
              )}
            >
              {pair.before ?? ''}
            </span>
          </div>
        ))}
      </div>

      {/* After */}
      <div className="flex-1">
        <div className="px-2 py-1 text-xs font-medium text-muted-foreground bg-muted/50 border-b">
          After
        </div>
        {pairs.map((pair, index) => (
          <div
            key={`after-${index}`}
            className={cn(
              'flex px-2 py-0.5',
              pair.after !== undefined && pair.before === undefined && 'bg-green-50 dark:bg-green-900/20'
            )}
          >
            <span className="w-8 flex-shrink-0 text-muted-foreground text-right pr-2 select-none">
              {pair.afterIdx ?? ''}
            </span>
            <span
              className={cn(
                'flex-1 whitespace-pre-wrap break-all',
                pair.after !== undefined && pair.before === undefined && 'text-green-800 dark:text-green-300'
              )}
            >
              {pair.after ?? ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Simple line-by-line diff algorithm
function computeDiff(before: string, after: string): DiffLine[] {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');
  const result: DiffLine[] = [];

  // Use simple LCS-based diff
  const lcs = computeLCS(beforeLines, afterLines);

  let beforeIdx = 0;
  let afterIdx = 0;
  let lcsIdx = 0;

  while (beforeIdx < beforeLines.length || afterIdx < afterLines.length) {
    if (lcsIdx < lcs.length && beforeIdx < beforeLines.length && beforeLines[beforeIdx] === lcs[lcsIdx]) {
      if (afterIdx < afterLines.length && afterLines[afterIdx] === lcs[lcsIdx]) {
        // Unchanged line
        result.push({
          type: 'unchanged',
          content: beforeLines[beforeIdx],
          lineNumberBefore: beforeIdx + 1,
          lineNumberAfter: afterIdx + 1,
        });
        beforeIdx++;
        afterIdx++;
        lcsIdx++;
      } else {
        // Added line in after
        result.push({
          type: 'add',
          content: afterLines[afterIdx],
          lineNumberAfter: afterIdx + 1,
        });
        afterIdx++;
      }
    } else if (beforeIdx < beforeLines.length) {
      // Removed line from before
      result.push({
        type: 'remove',
        content: beforeLines[beforeIdx],
        lineNumberBefore: beforeIdx + 1,
      });
      beforeIdx++;
    } else if (afterIdx < afterLines.length) {
      // Added line in after
      result.push({
        type: 'add',
        content: afterLines[afterIdx],
        lineNumberAfter: afterIdx + 1,
      });
      afterIdx++;
    }
  }

  return result;
}

// Compute Longest Common Subsequence
function computeLCS(a: string[], b: string[]): string[] {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to find LCS
  const lcs: string[] = [];
  let i = m;
  let j = n;

  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      lcs.unshift(a[i - 1]);
      i--;
      j--;
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }

  return lcs;
}

// Inline diff for single values
export function InlineDiff({
  before,
  after,
  className,
}: {
  before: string;
  after: string;
  className?: string;
}) {
  if (before === after) {
    return <span className={className}>{before}</span>;
  }

  return (
    <span className={cn('inline-flex items-center gap-1', className)}>
      <span className="line-through text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-1 rounded">
        {before}
      </span>
      <span className="text-muted-foreground">-&gt;</span>
      <span className="text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-1 rounded">
        {after}
      </span>
    </span>
  );
}
