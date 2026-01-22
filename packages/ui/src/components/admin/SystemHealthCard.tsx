'use client';

import * as React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Clock } from 'lucide-react';

import { cn } from '@/lib/utils';
import type { ServiceHealth } from '@/lib/api';

interface SystemHealthCardProps {
  health: ServiceHealth;
}

export function SystemHealthCard({ health }: SystemHealthCardProps) {
  const getStatusIcon = () => {
    switch (health.status) {
      case 'healthy':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (health.status) {
      case 'healthy':
        return 'border-green-500/30 bg-green-500/5';
      case 'degraded':
        return 'border-yellow-500/30 bg-yellow-500/5';
      case 'unhealthy':
        return 'border-red-500/30 bg-red-500/5';
      default:
        return 'border-gray-500/30 bg-gray-500/5';
    }
  };

  const getLatencyColor = () => {
    if (health.latency < 100) return 'text-green-600';
    if (health.latency < 300) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border p-3 transition-colors',
        getStatusColor()
      )}
    >
      <div className="flex items-center gap-3">
        {getStatusIcon()}
        <div>
          <p className="font-medium">{health.service}</p>
          <p className="text-xs text-muted-foreground capitalize">
            {health.status}
          </p>
        </div>
      </div>
      <div className="text-right">
        <p className={cn('text-sm font-medium', getLatencyColor())}>
          {health.latency}ms
        </p>
        <p className="text-xs text-muted-foreground">
          {health.uptime.toFixed(2)}% uptime
        </p>
      </div>
    </div>
  );
}
