'use client';

import * as React from 'react';
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Globe,
  User,
  XCircle,
} from 'lucide-react';

import { cn } from '@/lib/utils';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  category: string;
  actor: {
    id: string;
    name: string;
    email: string;
    type: 'user' | 'system' | 'api';
  };
  resource: {
    type: string;
    id: string;
    name: string;
  };
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  status: 'success' | 'failure';
}

interface AuditLogTableProps {
  logs: AuditLogEntry[];
  getCategoryColor: (category: string) => string;
}

export function AuditLogTable({ logs, getCategoryColor }: AuditLogTableProps) {
  const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const getActorIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <User className="h-4 w-4" />;
      case 'system':
        return <Globe className="h-4 w-4" />;
      case 'api':
        return <Globe className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const formatAction = (action: string) => {
    return action
      .split('.')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' > ');
  };

  return (
    <div className="rounded-md border overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="w-8 p-3"></th>
            <th className="p-3 text-left text-sm font-medium">Timestamp</th>
            <th className="p-3 text-left text-sm font-medium">Action</th>
            <th className="p-3 text-left text-sm font-medium">Category</th>
            <th className="p-3 text-left text-sm font-medium">Actor</th>
            <th className="p-3 text-left text-sm font-medium">Resource</th>
            <th className="p-3 text-left text-sm font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <React.Fragment key={log.id}>
              <tr
                className={cn(
                  'border-b cursor-pointer hover:bg-muted/50 transition-colors',
                  expandedRows.has(log.id) && 'bg-muted/30',
                  log.status === 'failure' && 'bg-red-500/5'
                )}
                onClick={() => toggleRow(log.id)}
              >
                <td className="p-3">
                  <button className="text-muted-foreground">
                    {expandedRows.has(log.id) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </button>
                </td>
                <td className="p-3 text-sm text-muted-foreground whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="p-3">
                  <span className="font-medium text-sm">{formatAction(log.action)}</span>
                </td>
                <td className="p-3">
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
                      getCategoryColor(log.category)
                    )}
                  >
                    {log.category}
                  </span>
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">
                      {getActorIcon(log.actor.type)}
                    </span>
                    <div>
                      <p className="text-sm font-medium">{log.actor.name}</p>
                      <p className="text-xs text-muted-foreground">{log.actor.email}</p>
                    </div>
                  </div>
                </td>
                <td className="p-3">
                  <div>
                    <p className="text-sm">{log.resource.name}</p>
                    <p className="text-xs text-muted-foreground">{log.resource.type}</p>
                  </div>
                </td>
                <td className="p-3">
                  {log.status === 'success' ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </td>
              </tr>
              {expandedRows.has(log.id) && (
                <tr className="bg-muted/20 border-b">
                  <td colSpan={7} className="p-4">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          Details
                        </p>
                        <pre className="text-xs bg-muted rounded p-2 overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          IP Address
                        </p>
                        <p className="text-sm font-mono">{log.ipAddress}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          User Agent
                        </p>
                        <p className="text-xs text-muted-foreground break-all">
                          {log.userAgent}
                        </p>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>

      {logs.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No audit logs found for the selected filters
        </div>
      )}
    </div>
  );
}
