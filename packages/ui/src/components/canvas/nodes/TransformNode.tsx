'use client';

import * as React from 'react';
import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import {
  GitBranch,
  Filter,
  Combine,
  Split,
  ArrowRightLeft,
  Calculator,
  Type,
  Calendar,
  Loader2,
  CheckCircle2,
  XCircle,
  Sparkles,
} from 'lucide-react';

export interface TransformNodeData {
  label: string;
  objectType?: string;
  transform?: {
    type:
      | 'filter'
      | 'join'
      | 'aggregate'
      | 'map'
      | 'split'
      | 'dedupe'
      | 'cast'
      | 'date_extract'
      | 'ontology_mapping'
      | 'custom';
    schema?: Record<string, unknown>;
    expression?: string;
  };
  config?: Record<string, unknown>;
  status?: 'idle' | 'running' | 'success' | 'error';
  description?: string;
  inputCount?: number;
  outputCount?: number;
}

const transformIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  filter: Filter,
  join: Combine,
  aggregate: Calculator,
  map: ArrowRightLeft,
  split: Split,
  dedupe: GitBranch,
  cast: Type,
  date_extract: Calendar,
  ontology_mapping: Sparkles,
  custom: GitBranch,
  default: GitBranch,
};

const statusIndicators: Record<string, { icon: React.ReactNode; className: string }> = {
  idle: {
    icon: null,
    className: '',
  },
  running: {
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
    className: 'text-amber-500',
  },
  success: {
    icon: <CheckCircle2 className="h-3 w-3" />,
    className: 'text-green-500',
  },
  error: {
    icon: <XCircle className="h-3 w-3" />,
    className: 'text-red-500',
  },
};

function TransformNodeComponent({ data, selected }: NodeProps<TransformNodeData>) {
  const transformType = data.transform?.type || 'custom';
  const Icon = transformIcons[transformType] || transformIcons.default;
  const status = data.status || 'idle';
  const statusConfig = statusIndicators[status];

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 min-w-[200px] max-w-[280px]',
        'bg-zinc-900 shadow-lg transition-all',
        selected
          ? 'border-violet-500 shadow-violet-500/20'
          : 'border-violet-500/50 hover:border-violet-500/70',
        status === 'running' && 'animate-pulse',
        status === 'error' && 'border-red-500/50'
      )}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className={cn(
          'w-3 h-3 bg-violet-500 border-2 border-zinc-900',
          '!left-[-6px]'
        )}
      />

      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex items-center justify-center w-8 h-8 rounded-md bg-violet-500/20 text-violet-400">
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-medium text-zinc-100 truncate">
              {data.label}
            </span>
            <span className="text-xs text-zinc-500 capitalize">
              {transformType.replace('_', ' ')}
            </span>
          </div>
        </div>

        {/* Status Indicator */}
        {statusConfig.icon && (
          <div className={cn('flex items-center', statusConfig.className)}>
            {statusConfig.icon}
          </div>
        )}
      </div>

      {/* Object Type (for ontology mapping) */}
      {data.objectType && (
        <div className="mt-2 flex items-center gap-1.5 text-xs">
          <Sparkles className="h-3 w-3 text-violet-400" />
          <span className="text-zinc-400">Target:</span>
          <span className="text-violet-300 font-medium">{data.objectType}</span>
        </div>
      )}

      {/* Description */}
      {data.description && (
        <p className="mt-2 text-xs text-zinc-500 line-clamp-2">
          {data.description}
        </p>
      )}

      {/* Transform Expression Preview */}
      {data.transform?.expression && (
        <div className="mt-2 pt-2 border-t border-zinc-800">
          <code className="text-xs text-violet-300/80 font-mono truncate block">
            {data.transform.expression.length > 40
              ? `${data.transform.expression.slice(0, 40)}...`
              : data.transform.expression}
          </code>
        </div>
      )}

      {/* Stats */}
      {(data.inputCount !== undefined || data.outputCount !== undefined) && (
        <div className="mt-2 pt-2 border-t border-zinc-800 flex items-center gap-3 text-xs text-zinc-500">
          {data.inputCount !== undefined && (
            <span>In: {data.inputCount.toLocaleString()}</span>
          )}
          {data.outputCount !== undefined && (
            <span>Out: {data.outputCount.toLocaleString()}</span>
          )}
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className={cn(
          'w-3 h-3 bg-violet-500 border-2 border-zinc-900',
          '!right-[-6px]'
        )}
      />

      {/* Node Type Indicator */}
      <div className="absolute -top-2 -left-2 px-1.5 py-0.5 bg-violet-500/20 border border-violet-500/30 rounded text-[10px] font-medium text-violet-400 uppercase">
        Transform
      </div>
    </div>
  );
}

export const TransformNode = memo(TransformNodeComponent);
