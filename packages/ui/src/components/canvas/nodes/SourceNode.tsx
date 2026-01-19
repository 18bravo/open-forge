'use client';

import * as React from 'react';
import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import {
  Database,
  Cloud,
  FileSpreadsheet,
  Globe,
  HardDrive,
  Server,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

export interface SourceNodeData {
  label: string;
  connectorType?: 'postgresql' | 's3' | 'rest' | 'csv' | 'mysql' | 'mongodb' | 'snowflake' | 'bigquery';
  config?: Record<string, unknown>;
  status?: 'idle' | 'running' | 'success' | 'error';
  description?: string;
  lastRun?: string;
  recordCount?: number;
}

const connectorIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  postgresql: Database,
  mysql: Database,
  mongodb: Database,
  snowflake: Server,
  bigquery: Cloud,
  s3: Cloud,
  rest: Globe,
  csv: FileSpreadsheet,
  default: HardDrive,
};

const connectorColors: Record<string, string> = {
  postgresql: 'text-blue-400',
  mysql: 'text-orange-400',
  mongodb: 'text-green-400',
  snowflake: 'text-cyan-400',
  bigquery: 'text-blue-500',
  s3: 'text-orange-500',
  rest: 'text-purple-400',
  csv: 'text-emerald-400',
  default: 'text-zinc-400',
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

function SourceNodeComponent({ data, selected }: NodeProps<SourceNodeData>) {
  const connectorType = data.connectorType || 'default';
  const Icon = connectorIcons[connectorType] || connectorIcons.default;
  const iconColor = connectorColors[connectorType] || connectorColors.default;
  const status = data.status || 'idle';
  const statusConfig = statusIndicators[status];

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 min-w-[200px] max-w-[280px]',
        'bg-zinc-900 shadow-lg transition-all',
        selected
          ? 'border-green-500 shadow-green-500/20'
          : 'border-green-500/50 hover:border-green-500/70',
        status === 'running' && 'animate-pulse',
        status === 'error' && 'border-red-500/50'
      )}
    >
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
            <span className="text-xs text-zinc-500 uppercase tracking-wide">
              {connectorType}
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

      {/* Metadata */}
      {(data.lastRun || data.recordCount !== undefined) && (
        <div className="mt-2 pt-2 border-t border-zinc-800 flex items-center gap-3 text-xs text-zinc-500">
          {data.lastRun && <span>Last: {data.lastRun}</span>}
          {data.recordCount !== undefined && (
            <span>{data.recordCount.toLocaleString()} records</span>
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

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className={cn(
          'w-3 h-3 bg-green-500 border-2 border-zinc-900',
          '!right-[-6px]'
        )}
      />

      {/* Node Type Indicator */}
      <div className="absolute -top-2 -left-2 px-1.5 py-0.5 bg-green-500/20 border border-green-500/30 rounded text-[10px] font-medium text-green-400 uppercase">
        Source
      </div>
    </div>
  );
}

export const SourceNode = memo(SourceNodeComponent);
