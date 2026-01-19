'use client';

import * as React from 'react';
import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import {
  Database,
  Cloud,
  FileOutput,
  Globe,
  HardDrive,
  Network,
  Loader2,
  CheckCircle2,
  XCircle,
  Share2,
} from 'lucide-react';

export interface DestinationNodeData {
  label: string;
  destinationType?:
    | 'graph'
    | 'postgresql'
    | 's3'
    | 'snowflake'
    | 'bigquery'
    | 'iceberg'
    | 'api'
    | 'file';
  config?: Record<string, unknown>;
  status?: 'idle' | 'running' | 'success' | 'error';
  description?: string;
  lastSync?: string;
  recordsWritten?: number;
}

const destinationIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  graph: Network,
  postgresql: Database,
  s3: Cloud,
  snowflake: Cloud,
  bigquery: Cloud,
  iceberg: HardDrive,
  api: Globe,
  file: FileOutput,
  default: Share2,
};

const destinationColors: Record<string, string> = {
  graph: 'text-blue-400',
  postgresql: 'text-blue-500',
  s3: 'text-orange-400',
  snowflake: 'text-cyan-400',
  bigquery: 'text-blue-400',
  iceberg: 'text-teal-400',
  api: 'text-purple-400',
  file: 'text-emerald-400',
  default: 'text-blue-400',
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

function DestinationNodeComponent({ data, selected }: NodeProps<DestinationNodeData>) {
  const destinationType = data.destinationType || 'default';
  const Icon = destinationIcons[destinationType] || destinationIcons.default;
  const iconColor = destinationColors[destinationType] || destinationColors.default;
  const status = data.status || 'idle';
  const statusConfig = statusIndicators[status];

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 min-w-[200px] max-w-[280px]',
        'bg-zinc-900 shadow-lg transition-all',
        selected
          ? 'border-blue-500 shadow-blue-500/20'
          : 'border-blue-500/50 hover:border-blue-500/70',
        status === 'running' && 'animate-pulse',
        status === 'error' && 'border-red-500/50'
      )}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className={cn(
          'w-3 h-3 bg-blue-500 border-2 border-zinc-900',
          '!left-[-6px]'
        )}
      />

      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={cn(
              'flex items-center justify-center w-8 h-8 rounded-md bg-zinc-800',
              iconColor
            )}
          >
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-medium text-zinc-100 truncate">
              {data.label}
            </span>
            <span className="text-xs text-zinc-500 capitalize">
              {destinationType === 'graph' ? 'Knowledge Graph' : destinationType}
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

      {/* Description */}
      {data.description && (
        <p className="mt-2 text-xs text-zinc-500 line-clamp-2">
          {data.description}
        </p>
      )}

      {/* Sync Info */}
      {(data.lastSync || data.recordsWritten !== undefined) && (
        <div className="mt-2 pt-2 border-t border-zinc-800 flex items-center gap-3 text-xs text-zinc-500">
          {data.lastSync && <span>Last sync: {data.lastSync}</span>}
          {data.recordsWritten !== undefined && (
            <span>{data.recordsWritten.toLocaleString()} written</span>
          )}
        </div>
      )}

      {/* Config Preview */}
      {data.config && Object.keys(data.config).length > 0 && (
        <div className="mt-2 pt-2 border-t border-zinc-800">
          <div className="text-xs text-zinc-600">
            {Object.entries(data.config)
              .slice(0, 2)
              .map(([key, value]) => (
                <div key={key} className="flex items-center gap-1 truncate">
                  <span className="text-zinc-500">{key}:</span>
                  <span className="text-zinc-400 truncate">
                    {typeof value === 'string' && value.includes('***')
                      ? '***'
                      : String(value)}
                  </span>
                </div>
              ))}
            {Object.keys(data.config).length > 2 && (
              <span className="text-zinc-600">
                +{Object.keys(data.config).length - 2} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Node Type Indicator */}
      <div className="absolute -top-2 -left-2 px-1.5 py-0.5 bg-blue-500/20 border border-blue-500/30 rounded text-[10px] font-medium text-blue-400 uppercase">
        Destination
      </div>
    </div>
  );
}

export const DestinationNode = memo(DestinationNodeComponent);
