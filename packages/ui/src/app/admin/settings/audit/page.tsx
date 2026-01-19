'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Download,
  Globe,
  Loader2,
  RefreshCw,
  Search,
  User,
  XCircle,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useAuditLogs } from '@/lib/hooks';
import type { AuditLogEntry } from '@/lib/api';

export default function AuditLogPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [categoryFilter, setCategoryFilter] = React.useState<string>('all');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());
  const logsPerPage = 25;

  const { data: logsData, isLoading, error, refetch } = useAuditLogs({
    page: currentPage,
    page_size: logsPerPage,
    category: categoryFilter !== 'all' ? categoryFilter : undefined,
  });

  const logs = logsData?.items || [];
  const totalPages = logsData?.total_pages || 1;

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

  const handleExport = (format: 'csv' | 'json') => {
    const dataStr = format === 'json'
      ? JSON.stringify(logs, null, 2)
      : convertToCSV(logs);
    const dataBlob = new Blob([dataStr], { type: format === 'json' ? 'application/json' : 'text/csv' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit-log-${new Date().toISOString()}.${format}`;
    link.click();
  };

  const convertToCSV = (data: AuditLogEntry[]) => {
    const headers = ['Timestamp', 'Action', 'Category', 'Actor', 'Actor Type', 'Resource Type', 'Resource ID', 'IP Address'];
    const rows = data.map(log => [
      log.timestamp,
      log.action,
      log.category,
      log.actor,
      log.actor_type,
      log.resource_type,
      log.resource_id,
      log.ip_address || '',
    ]);
    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  };

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resource_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resource_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'auth':
        return 'bg-purple-500/10 text-purple-600 border-purple-500/30';
      case 'data':
        return 'bg-blue-500/10 text-blue-600 border-blue-500/30';
      case 'config':
        return 'bg-orange-500/10 text-orange-600 border-orange-500/30';
      case 'pipeline':
        return 'bg-green-500/10 text-green-600 border-green-500/30';
      case 'agent':
        return 'bg-cyan-500/10 text-cyan-600 border-cyan-500/30';
      case 'user':
        return 'bg-pink-500/10 text-pink-600 border-pink-500/30';
      case 'system':
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
      default:
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
    }
  };

  const getActorIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <User className="h-4 w-4" />;
      case 'system':
      case 'agent':
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

  // Stats from current page data
  const stats = {
    total: logsData?.total || 0,
    byCategory: {
      auth: logs.filter((l) => l.category === 'auth').length,
      data: logs.filter((l) => l.category === 'data').length,
      config: logs.filter((l) => l.category === 'config').length,
      pipeline: logs.filter((l) => l.category === 'pipeline').length,
    },
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-lg font-medium">Failed to load audit logs</p>
        <p className="text-sm text-muted-foreground">{error.message}</p>
        <Button onClick={() => refetch()}>Try Again</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/admin/settings">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Audit Log</h1>
            <p className="text-muted-foreground">
              View system activity and security events
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('json')}>
            <Download className="mr-2 h-4 w-4" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Total Events</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-purple-600">{stats.byCategory.auth}</div>
            <p className="text-xs text-muted-foreground">Auth Events (this page)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-600">{stats.byCategory.data}</div>
            <p className="text-xs text-muted-foreground">Data Events (this page)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">{stats.byCategory.pipeline}</div>
            <p className="text-xs text-muted-foreground">Pipeline Events (this page)</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Activity Log</CardTitle>
              <CardDescription>
                {filteredLogs.length} events on this page
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Categories</option>
                <option value="auth">Authentication</option>
                <option value="data">Data</option>
                <option value="config">Configuration</option>
                <option value="pipeline">Pipeline</option>
                <option value="agent">Agent</option>
                <option value="user">User</option>
                <option value="system">System</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No audit logs found for the selected filters
            </div>
          ) : (
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
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log) => (
                    <React.Fragment key={log.id}>
                      <tr
                        className={cn(
                          'border-b cursor-pointer hover:bg-muted/50 transition-colors',
                          expandedRows.has(log.id) && 'bg-muted/30'
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
                              {getActorIcon(log.actor_type)}
                            </span>
                            <div>
                              <p className="text-sm font-medium">{log.actor}</p>
                              <p className="text-xs text-muted-foreground">{log.actor_type}</p>
                            </div>
                          </div>
                        </td>
                        <td className="p-3">
                          <div>
                            <p className="text-sm">{log.resource_id}</p>
                            <p className="text-xs text-muted-foreground">{log.resource_type}</p>
                          </div>
                        </td>
                      </tr>
                      {expandedRows.has(log.id) && (
                        <tr className="bg-muted/20 border-b">
                          <td colSpan={6} className="p-4">
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
                                <p className="text-sm font-mono">{log.ip_address || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-muted-foreground mb-1">
                                  Event ID
                                </p>
                                <p className="text-xs text-muted-foreground break-all">
                                  {log.id}
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
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
