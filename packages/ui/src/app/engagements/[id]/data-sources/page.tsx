'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/engagements';
import { useEngagement } from '@/lib/hooks/use-engagement';
import { useDataSource, useTestDataSourceConnection } from '@/lib/hooks/use-data-source';
import type { DataSource, DataSourceStatus } from '@/lib/api';
import { formatRelativeTime } from '@/lib/utils';
import {
  AlertCircle,
  CheckCircle2,
  Database,
  ExternalLink,
  Loader2,
  Plus,
  RefreshCw,
  Settings,
} from 'lucide-react';

const sourceTypeIcons: Record<string, React.ReactNode> = {
  postgresql: <Database className="h-5 w-5 text-blue-500" />,
  mysql: <Database className="h-5 w-5 text-orange-500" />,
  s3: <Database className="h-5 w-5 text-green-500" />,
  gcs: <Database className="h-5 w-5 text-blue-400" />,
  azure_blob: <Database className="h-5 w-5 text-blue-600" />,
  iceberg: <Database className="h-5 w-5 text-cyan-500" />,
  delta: <Database className="h-5 w-5 text-red-500" />,
  parquet: <Database className="h-5 w-5 text-purple-500" />,
  csv: <Database className="h-5 w-5 text-gray-500" />,
  api: <Database className="h-5 w-5 text-indigo-500" />,
  kafka: <Database className="h-5 w-5 text-gray-700" />,
};

interface DataSourcesPageProps {
  params: Promise<{ id: string }>;
}

export default function DataSourcesPage({ params }: DataSourcesPageProps) {
  const { id } = React.use(params);
  const { data: engagement, isLoading: engLoading, error: engError } = useEngagement(id);

  if (engLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (engError || !engagement) {
    return (
      <Card className="flex flex-col items-center justify-center py-12 text-center">
        <h3 className="text-lg font-medium">Error loading engagement</h3>
        <p className="text-sm text-muted-foreground">
          {engError?.message || 'Engagement not found'}
        </p>
      </Card>
    );
  }

  const dataSourceIds = engagement.data_sources.map((ds) => ds.source_id);

  return (
    <DataSourcesList
      dataSourceIds={dataSourceIds}
      engagementId={params.id}
    />
  );
}

interface DataSourcesListProps {
  dataSourceIds: string[];
  engagementId: string;
}

function DataSourcesList({ dataSourceIds, engagementId }: DataSourcesListProps) {
  const [testingId, setTestingId] = React.useState<string | null>(null);
  const testConnectionMutation = useTestDataSourceConnection();

  // Fetch each data source individually
  const dataSourceQueries = dataSourceIds.map((id) => ({
    id,
    ...useDataSource(id),
  }));

  const isLoading = dataSourceQueries.some((q) => q.isLoading);
  const dataSources = dataSourceQueries
    .filter((q) => q.data)
    .map((q) => q.data as DataSource);

  const handleTestConnection = async (sourceId: string) => {
    setTestingId(sourceId);
    try {
      await testConnectionMutation.mutateAsync(sourceId);
    } finally {
      setTestingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Data Sources</h2>
          <p className="text-sm text-muted-foreground">
            {dataSources.length} data source{dataSources.length !== 1 ? 's' : ''} connected to this engagement
          </p>
        </div>
        <Button asChild>
          <Link href="/data-sources/new">
            <Plus className="mr-2 h-4 w-4" />
            Add Data Source
          </Link>
        </Button>
      </div>

      {/* Data Source List */}
      <div className="grid gap-4">
        {dataSources.map((source) => (
          <DataSourceCard
            key={source.id}
            source={source}
            isTesting={testingId === source.id}
            onTest={() => handleTestConnection(source.id)}
          />
        ))}
      </div>

      {/* Empty State */}
      {dataSources.length === 0 && (
        <Card className="flex flex-col items-center justify-center py-12 text-center">
          <Database className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">No data sources</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Connect data sources to start processing data in this engagement.
          </p>
          <Button asChild>
            <Link href="/data-sources/new">
              <Plus className="mr-2 h-4 w-4" />
              Add Data Source
            </Link>
          </Button>
        </Card>
      )}
    </div>
  );
}

interface DataSourceCardProps {
  source: DataSource;
  isTesting: boolean;
  onTest: () => void;
}

function DataSourceCard({ source, isTesting, onTest }: DataSourceCardProps) {
  const icon = sourceTypeIcons[source.source_type] || <Database className="h-5 w-5" />;

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
              {icon}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">{source.name}</h3>
                <ConnectionStatusBadge status={source.status} />
              </div>
              {source.description && (
                <p className="text-sm text-muted-foreground">{source.description}</p>
              )}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="capitalize">{source.source_type.replace('_', ' ')}</span>
                {source.last_tested_at && (
                  <span>
                    Last tested {formatRelativeTime(source.last_tested_at)}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:flex-shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={onTest}
              disabled={isTesting}
            >
              {isTesting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Test
                </>
              )}
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href={`/data-sources/${source.id}`}>
                <Settings className="mr-2 h-4 w-4" />
                Configure
              </Link>
            </Button>
            <Button variant="ghost" size="icon" asChild>
              <Link href={`/data-sources/${source.id}`}>
                <ExternalLink className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>

        {/* Connection Details */}
        <div className="mt-4 pt-4 border-t">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 text-sm">
            {Object.entries(source.connection_config)
              .filter(([key]) => !key.toLowerCase().includes('password') && !key.toLowerCase().includes('key'))
              .slice(0, 4)
              .map(([key, value]) => (
                <div key={key}>
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>{' '}
                  <span className="font-mono">{String(value)}</span>
                </div>
              ))}
          </div>
        </div>

        {/* Tags */}
        {source.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {source.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground text-xs"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ConnectionStatusBadge({ status }: { status: DataSourceStatus }) {
  const config: Record<DataSourceStatus, { icon: React.ReactNode; className: string; label: string }> = {
    active: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      className: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
      label: 'Connected',
    },
    inactive: {
      icon: <AlertCircle className="h-3 w-3" />,
      className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
      label: 'Inactive',
    },
    error: {
      icon: <AlertCircle className="h-3 w-3" />,
      className: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
      label: 'Error',
    },
    testing: {
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      label: 'Testing',
    },
  };

  const { icon, className, label } = config[status];

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {icon}
      {label}
    </span>
  );
}
