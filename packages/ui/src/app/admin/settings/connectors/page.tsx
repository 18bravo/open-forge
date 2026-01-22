'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Cloud,
  Database,
  Edit,
  FileJson,
  Loader2,
  MoreVertical,
  Plus,
  RefreshCw,
  Search,
  Server,
  Trash2,
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
import { useConnectors, useTestConnector } from '@/lib/hooks';

const connectorTypes = [
  { id: 'database', name: 'Database', icon: Database },
  { id: 'cloud_service', name: 'Cloud Storage', icon: Cloud },
  { id: 'api', name: 'API', icon: Server },
  { id: 'file_storage', name: 'File System', icon: FileJson },
  { id: 'message_queue', name: 'Message Queue', icon: Server },
];

export default function ConnectorsPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [typeFilter, setTypeFilter] = React.useState<string>('all');
  const [testingConnectorId, setTestingConnectorId] = React.useState<string | null>(null);

  const { data: connectorsData, isLoading, error, refetch } = useConnectors({
    type: typeFilter !== 'all' ? typeFilter : undefined,
  });
  const testConnector = useTestConnector();

  const connectors = connectorsData?.items || [];

  const handleTestConnector = async (connectorId: string) => {
    setTestingConnectorId(connectorId);
    try {
      await testConnector.mutateAsync(connectorId);
    } finally {
      setTestingConnectorId(null);
    }
  };

  const handleTestAll = async () => {
    for (const connector of connectors) {
      setTestingConnectorId(connector.id);
      try {
        await testConnector.mutateAsync(connector.id);
      } catch {
        // Continue testing other connectors even if one fails
      }
    }
    setTestingConnectorId(null);
  };

  const filteredConnectors = connectors.filter((connector) => {
    const matchesSearch =
      connector.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.provider.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'inactive':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getTypeIcon = (type: string) => {
    const typeInfo = connectorTypes.find((t) => t.id === type);
    if (!typeInfo) return Database;
    return typeInfo.icon;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-600 border-green-500/30';
      case 'inactive':
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
      case 'error':
        return 'bg-red-500/10 text-red-600 border-red-500/30';
      default:
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
    }
  };

  // Stats
  const stats = {
    total: connectors.length,
    active: connectors.filter((c) => c.status === 'active').length,
    inactive: connectors.filter((c) => c.status === 'inactive').length,
    error: connectors.filter((c) => c.status === 'error').length,
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
        <p className="text-lg font-medium">Failed to load connectors</p>
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
            <h1 className="text-3xl font-bold tracking-tight">Connectors</h1>
            <p className="text-muted-foreground">
              Manage data source and destination connections
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestAll}
            disabled={testingConnectorId !== null}
          >
            <RefreshCw
              className={cn('mr-2 h-4 w-4', testingConnectorId !== null && 'animate-spin')}
            />
            Test All
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Connector
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Total Connectors</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-xs text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-gray-600">{stats.inactive}</div>
              <XCircle className="h-5 w-5 text-gray-500" />
            </div>
            <p className="text-xs text-muted-foreground">Inactive</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold text-red-600">{stats.error}</div>
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground">Error</p>
          </CardContent>
        </Card>
      </div>

      {/* Connector Types Quick Add */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Add Connector</CardTitle>
          <CardDescription>
            Select a connector type to add a new connection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            {connectorTypes.map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.id}
                  className="flex items-center gap-3 rounded-lg border p-4 text-left hover:bg-muted/50 transition-colors"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{type.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {connectors.filter((c) => c.type === type.id).length} configured
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Connectors List */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>All Connectors</CardTitle>
              <CardDescription>
                {filteredConnectors.length} connectors configured
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search connectors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="all">All Types</option>
                {connectorTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredConnectors.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No connectors found
            </div>
          ) : (
            <div className="space-y-4">
              {filteredConnectors.map((connector) => {
                const TypeIcon = getTypeIcon(connector.type);
                const isTesting = testingConnectorId === connector.id;
                return (
                  <div
                    key={connector.id}
                    className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          'flex h-12 w-12 items-center justify-center rounded-lg',
                          connector.status === 'active' && 'bg-green-500/10',
                          connector.status === 'inactive' && 'bg-gray-500/10',
                          connector.status === 'error' && 'bg-red-500/10'
                        )}
                      >
                        <TypeIcon
                          className={cn(
                            'h-6 w-6',
                            connector.status === 'active' && 'text-green-600',
                            connector.status === 'inactive' && 'text-gray-600',
                            connector.status === 'error' && 'text-red-600'
                          )}
                        />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{connector.name}</p>
                          <span
                            className={cn(
                              'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
                              getStatusBadge(connector.status)
                            )}
                          >
                            {getStatusIcon(connector.status)}
                            <span className="ml-1">{connector.status}</span>
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {connector.provider}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Last tested:{' '}
                          {connector.last_tested
                            ? new Date(connector.last_tested).toLocaleString()
                            : 'Never'}
                          {connector.last_test_success !== null && (
                            <span className={connector.last_test_success ? 'text-green-600' : 'text-red-600'}>
                              {' '}({connector.last_test_success ? 'passed' : 'failed'})
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Test Connection"
                        onClick={() => handleTestConnector(connector.id)}
                        disabled={isTesting}
                      >
                        <RefreshCw className={cn('h-4 w-4', isTesting && 'animate-spin')} />
                      </Button>
                      <Button variant="ghost" size="icon" title="Edit">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Delete">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="More">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
