'use client';

import * as React from 'react';
import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { DataSourceSummary, DataSourceType, DataSourceStatus } from '@/lib/api';
import { formatRelativeTime } from '@/lib/utils';
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Database,
  Filter,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Settings,
  X,
} from 'lucide-react';
import { useDataSources, useTestDataSourceConnection } from '@/lib/hooks/use-data-source';

const typeOptions: { value: DataSourceType | 'all'; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 's3', label: 'Amazon S3' },
  { value: 'gcs', label: 'Google Cloud Storage' },
  { value: 'azure_blob', label: 'Azure Blob' },
  { value: 'iceberg', label: 'Apache Iceberg' },
  { value: 'delta', label: 'Delta Lake' },
  { value: 'parquet', label: 'Parquet' },
  { value: 'csv', label: 'CSV' },
  { value: 'api', label: 'API' },
  { value: 'kafka', label: 'Kafka' },
];

const statusOptions: { value: DataSourceStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'error', label: 'Error' },
  { value: 'testing', label: 'Testing' },
];

const sourceTypeColors: Record<DataSourceType, string> = {
  postgresql: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
  mysql: 'bg-orange-100 text-orange-600 dark:bg-orange-900 dark:text-orange-400',
  s3: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
  gcs: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
  azure_blob: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
  iceberg: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900 dark:text-cyan-400',
  delta: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
  parquet: 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
  csv: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  api: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400',
  kafka: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
};

const statusIcons: Record<DataSourceStatus, React.ReactNode> = {
  active: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  inactive: <AlertCircle className="h-4 w-4 text-gray-400" />,
  error: <AlertCircle className="h-4 w-4 text-red-500" />,
  testing: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
};

export default function DataSourcesPage() {
  return (
    <Suspense fallback={
      <div className="container py-6 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <DataSourcesPageContent />
    </Suspense>
  );
}

function DataSourcesPageContent() {
  const searchParams = useSearchParams();

  const [search, setSearch] = React.useState(searchParams.get('search') || '');
  const [type, setType] = React.useState<DataSourceType | 'all'>(
    (searchParams.get('type') as DataSourceType) || 'all'
  );
  const [status, setStatus] = React.useState<DataSourceStatus | 'all'>(
    (searchParams.get('status') as DataSourceStatus) || 'all'
  );
  const [page, setPage] = React.useState(Number(searchParams.get('page')) || 1);
  const [showFilters, setShowFilters] = React.useState(false);

  const pageSize = 10;

  // Fetch data sources from API
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useDataSources({
    page,
    page_size: pageSize,
    type: type === 'all' ? undefined : type,
    status: status === 'all' ? undefined : status,
    search: search || undefined,
  });

  const testConnection = useTestDataSourceConnection();

  // Extract data sources from paginated response
  const dataSources = React.useMemo(() => {
    return (data?.items ?? []) as DataSourceSummary[];
  }, [data]);

  const totalCount = data?.total ?? 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  const clearFilters = () => {
    setSearch('');
    setType('all');
    setStatus('all');
    setPage(1);
  };

  const hasActiveFilters = search || type !== 'all' || status !== 'all';

  const handleTestConnection = async (id: string) => {
    await testConnection.mutateAsync(id);
  };

  return (
    <div className="container py-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
          <p className="text-muted-foreground">
            Manage connections to your data sources
          </p>
        </div>
        <Button asChild>
          <Link href="/data-sources/new">
            <Plus className="mr-2 h-4 w-4" />
            Add Data Source
          </Link>
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            {/* Search Bar */}
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search data sources..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="pl-9"
                />
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowFilters(!showFilters)}
                className={showFilters ? 'bg-accent' : ''}
              >
                <Filter className="h-4 w-4" />
              </Button>
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="mr-1 h-4 w-4" />
                  Clear
                </Button>
              )}
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="grid gap-4 sm:grid-cols-2 pt-2 border-t">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Type</label>
                  <Select
                    value={type}
                    onValueChange={(value) => {
                      setType(value as DataSourceType | 'all');
                      setPage(1);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {typeOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <Select
                    value={status}
                    onValueChange={(value) => {
                      setStatus(value as DataSourceStatus | 'all');
                      setPage(1);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {/* Results Count */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin inline mr-2" />
            ) : (
              <>
                {totalCount} data source{totalCount !== 1 ? 's' : ''} found
              </>
            )}
          </span>
          {totalPages > 1 && (
            <span>
              Page {page} of {totalPages}
            </span>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Error State */}
        {isError && !isLoading && (
          <Card className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
            <h3 className="text-lg font-medium">Failed to load data sources</h3>
            <p className="text-sm text-muted-foreground mb-4">
              There was an error loading the data sources. Please try again.
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </Card>
        )}

        {/* Data Source Grid */}
        {!isLoading && !isError && dataSources.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {dataSources.map((source) => (
              <DataSourceCard
                key={source.id}
                source={source}
                isTesting={testConnection.isPending && testConnection.variables === source.id}
                onTest={() => handleTestConnection(source.id)}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !isError && dataSources.length === 0 && (
          <Card className="flex flex-col items-center justify-center py-12 text-center">
            <Database className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No data sources found</h3>
            <p className="text-sm text-muted-foreground mb-4">
              {hasActiveFilters
                ? 'Try adjusting your filters or search terms.'
                : 'Get started by adding your first data source.'}
            </p>
            {hasActiveFilters ? (
              <Button variant="outline" onClick={clearFilters}>
                Clear Filters
              </Button>
            ) : (
              <Button asChild>
                <Link href="/data-sources/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Data Source
                </Link>
              </Button>
            )}
          </Card>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                // Show first few pages, current page area, or last few pages
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <Button
                    key={pageNum}
                    variant={pageNum === page ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setPage(pageNum)}
                    className="w-8"
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

interface DataSourceCardProps {
  source: DataSourceSummary;
  isTesting: boolean;
  onTest: () => void;
}

function DataSourceCard({ source, isTesting, onTest }: DataSourceCardProps) {
  return (
    <Card className="group relative overflow-hidden transition-all hover:shadow-md hover:border-primary/50">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${sourceTypeColors[source.source_type]}`}>
              <Database className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base">{source.name}</CardTitle>
              <CardDescription className="text-xs capitalize">
                {source.source_type.replace('_', ' ')}
              </CardDescription>
            </div>
          </div>
          {statusIcons[source.status]}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Added {formatRelativeTime(source.created_at)}
          </span>
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.preventDefault();
                onTest();
              }}
              disabled={isTesting}
            >
              {isTesting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/data-sources/${source.id}`}>
                <Settings className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
      <Link href={`/data-sources/${source.id}`} className="absolute inset-0" />
    </Card>
  );
}
