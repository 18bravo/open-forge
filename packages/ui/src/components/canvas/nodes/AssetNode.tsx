'use client';

import * as React from 'react';
import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import {
  Box,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
} from 'lucide-react';

export interface AssetNodeData {
  label: string;
  assetKey?: string;
  description?: string;
  group?: string;
  computeKind?: string;
  status?: 'idle' | 'running' | 'success' | 'error' | 'stale';
  lastMaterialization?: string;
  partitions?: {
    total: number;
    materialized: number;
  };
  metadata?: Record<string, unknown>;
  hasUpstream?: boolean;
  hasDownstream?: boolean;
}

const statusIndicators: Record<
  string,
  { icon: React.ReactNode; className: string; bgClass: string }
> = {
  idle: {
    icon: null,
    className: 'text-zinc-500',
    bgClass: 'border-amber-500/50',
  },
  running: {
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
    className: 'text-amber-500',
    bgClass: 'border-amber-500 animate-pulse',
  },
  success: {
    icon: <CheckCircle2 className="h-3 w-3" />,
    className: 'text-green-500',
    bgClass: 'border-green-500/50',
  },
  error: {
    icon: <XCircle className="h-3 w-3" />,
    className: 'text-red-500',
    bgClass: 'border-red-500/50',
  },
  stale: {
    icon: <Clock className="h-3 w-3" />,
    className: 'text-yellow-500',
    bgClass: 'border-yellow-500/50',
  },
};

const computeKindColors: Record<string, string> = {
  python: 'bg-yellow-500/20 text-yellow-400',
  polars: 'bg-blue-500/20 text-blue-400',
  pandas: 'bg-purple-500/20 text-purple-400',
  sql: 'bg-cyan-500/20 text-cyan-400',
  spark: 'bg-orange-500/20 text-orange-400',
  dbt: 'bg-green-500/20 text-green-400',
  default: 'bg-zinc-500/20 text-zinc-400',
};

function AssetNodeComponent({ data, selected }: NodeProps<AssetNodeData>) {
  const status = data.status || 'idle';
  const statusConfig = statusIndicators[status];
  const hasUpstream = data.hasUpstream !== false;
  const hasDownstream = data.hasDownstream !== false;
  const computeKindClass =
    computeKindColors[data.computeKind || 'default'] || computeKindColors.default;

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 min-w-[200px] max-w-[280px]',
        'bg-zinc-900 shadow-lg transition-all',
        selected
          ? 'border-amber-500 shadow-amber-500/20'
          : statusConfig.bgClass,
        status === 'running' && 'animate-pulse'
      )}
    >
      {/* Input Handle (only if has upstream) */}
      {hasUpstream && (
        <Handle
          type="target"
          position={Position.Left}
          className={cn(
            'w-3 h-3 bg-amber-500 border-2 border-zinc-900',
            '!left-[-6px]'
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex items-center justify-center w-8 h-8 rounded-md bg-amber-500/20 text-amber-400">
            <Box className="w-5 h-5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-medium text-zinc-100 truncate">
              {data.label}
            </span>
            {data.assetKey && (
              <span className="text-xs text-zinc-500 font-mono truncate">
                {data.assetKey}
              </span>
            )}
          </div>
        </div>

        {/* Status Indicator */}
        {statusConfig.icon && (
          <div className={cn('flex items-center', statusConfig.className)}>
            {statusConfig.icon}
          </div>
        )}
      </div>

      {/* Group and Compute Kind */}
      <div className="mt-2 flex items-center gap-2 flex-wrap">
        {data.group && (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-zinc-800 text-[10px] text-zinc-400">
            <Layers className="h-2.5 w-2.5" />
            {data.group}
          </span>
        )}
        {data.computeKind && (
          <span
            className={cn(
              'inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium',
              computeKindClass
            )}
          >
            {data.computeKind}
          </span>
        )}
      </div>

      {/* Description */}
      {data.description && (
        <p className="mt-2 text-xs text-zinc-500 line-clamp-2">
          {data.description}
        </p>
      )}

      {/* Partitions */}
      {data.partitions && (
        <div className="mt-2 pt-2 border-t border-zinc-800">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500">Partitions</span>
            <span className="text-zinc-400">
              {data.partitions.materialized} / {data.partitions.total}
            </span>
          </div>
          <div className="mt-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full transition-all"
              style={{
                width: `${
                  (data.partitions.materialized / data.partitions.total) * 100
                }%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Last Materialization */}
      {data.lastMaterialization && (
        <div className="mt-2 pt-2 border-t border-zinc-800 text-xs text-zinc-500">
          Last run: {data.lastMaterialization}
        </div>
      )}

      {/* Metadata Preview */}
      {data.metadata && Object.keys(data.metadata).length > 0 && (
        <div className="mt-2 pt-2 border-t border-zinc-800">
          <div className="text-xs text-zinc-600">
            {Object.entries(data.metadata)
              .slice(0, 2)
              .map(([key, value]) => (
                <div key={key} className="flex items-center gap-1 truncate">
                  <span className="text-zinc-500">{key}:</span>
                  <span className="text-zinc-400 truncate">
                    {String(value)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Output Handle (only if has downstream) */}
      {hasDownstream && (
        <Handle
          type="source"
          position={Position.Right}
          className={cn(
            'w-3 h-3 bg-amber-500 border-2 border-zinc-900',
            '!right-[-6px]'
          )}
        />
      )}

      {/* Node Type Indicator */}
      <div className="absolute -top-2 -left-2 px-1.5 py-0.5 bg-amber-500/20 border border-amber-500/30 rounded text-[10px] font-medium text-amber-400 uppercase">
        Asset
      </div>
    </div>
  );
}

export const AssetNode = memo(AssetNodeComponent);
