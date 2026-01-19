'use client';

import * as React from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  EngagementCard,
  EngagementCardSkeleton,
} from '@/components/engagements';
import { useEngagements } from '@/lib/hooks/use-engagement';
import type { EngagementStatus, EngagementPriority } from '@/lib/api';
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Filter,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  X,
} from 'lucide-react';

const statusOptions: { value: EngagementStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending_approval', label: 'Pending Approval' },
  { value: 'approved', label: 'Approved' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'paused', label: 'Paused' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'failed', label: 'Failed' },
];

const priorityOptions: { value: EngagementPriority | 'all'; label: string }[] = [
  { value: 'all', label: 'All Priorities' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

export default function EngagementsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [search, setSearch] = React.useState(searchParams.get('search') || '');
  const [debouncedSearch, setDebouncedSearch] = React.useState(search);
  const [status, setStatus] = React.useState<EngagementStatus | 'all'>(
    (searchParams.get('status') as EngagementStatus) || 'all'
  );
  const [priority, setPriority] = React.useState<EngagementPriority | 'all'>(
    (searchParams.get('priority') as EngagementPriority) || 'all'
  );
  const [page, setPage] = React.useState(Number(searchParams.get('page')) || 1);
  const [showFilters, setShowFilters] = React.useState(false);

  const pageSize = 10;

  // Debounce search input
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Fetch engagements using the hook
  const { data, isLoading, isError, error, refetch, isFetching } = useEngagements({
    page,
    page_size: pageSize,
    status: status === 'all' ? undefined : status,
    priority: priority === 'all' ? undefined : priority,
    search: debouncedSearch || undefined,
  });

  const engagements = data?.items ?? [];
  const totalPages = data?.total_pages ?? 1;
  const totalCount = data?.total ?? 0;

  // Update URL with filters
  const updateFilters = React.useCallback(
    (updates: { search?: string; status?: string; priority?: string; page?: number }) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([key, value]) => {
        if (value && value !== 'all') {
          params.set(key, String(value));
        } else {
          params.delete(key);
        }
      });
      router.push(`/engagements?${params.toString()}`);
    },
    [router, searchParams]
  );

  const clearFilters = () => {
    setSearch('');
    setStatus('all');
    setPriority('all');
    setPage(1);
    router.push('/engagements');
  };

  const hasActiveFilters = search || status !== 'all' || priority !== 'all';

  // Error state
  if (isError) {
    return (
      <div className="container py-6 space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Engagements</h1>
            <p className="text-muted-foreground">
              Manage and monitor your data engagements
            </p>
          </div>
        </div>
        <Card className="flex flex-col items-center justify-center py-12 text-center">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h3 className="text-lg font-medium">Failed to load engagements</h3>
          <p className="text-sm text-muted-foreground mb-4">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
          <Button onClick={() => refetch()} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container py-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Engagements</h1>
          <p className="text-muted-foreground">
            Manage and monitor your data engagements
          </p>
        </div>
        <Button asChild>
          <Link href="/engagements/new">
            <Plus className="mr-2 h-4 w-4" />
            New Engagement
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
                  placeholder="Search engagements..."
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
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 pt-2 border-t">
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={status}
                    onValueChange={(value) => {
                      setStatus(value as EngagementStatus | 'all');
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
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select
                    value={priority}
                    onValueChange={(value) => {
                      setPriority(value as EngagementPriority | 'all');
                      setPage(1);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select priority" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorityOptions.map((option) => (
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
          <span className="flex items-center gap-2">
            {totalCount} engagement{totalCount !== 1 ? 's' : ''} found
            {isFetching && !isLoading && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
          </span>
          {totalPages > 1 && (
            <span>
              Page {page} of {totalPages}
            </span>
          )}
        </div>

        {/* Engagement Grid */}
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <EngagementCardSkeleton key={i} />
            ))}
          </div>
        ) : engagements.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {engagements.map((engagement) => (
              <EngagementCard key={engagement.id} engagement={engagement} />
            ))}
          </div>
        ) : (
          <Card className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No engagements found</h3>
            <p className="text-sm text-muted-foreground mb-4">
              {hasActiveFilters
                ? 'Try adjusting your filters or search terms.'
                : 'Get started by creating your first engagement.'}
            </p>
            {hasActiveFilters ? (
              <Button variant="outline" onClick={clearFilters}>
                Clear Filters
              </Button>
            ) : (
              <Button asChild>
                <Link href="/engagements/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Engagement
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
                // Show pages around current page
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
