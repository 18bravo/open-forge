'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Filter,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  BarChart3,
  ListFilter,
  Loader2,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ReviewItemCard, ReviewItemList } from '@/components/approvals/ReviewItemCard';
import {
  ReviewListItem,
  ReviewCategory,
  ReviewStatus,
  ReviewPriority,
  ReviewFilters,
  getReviewCategoryLabel,
  getPriorityLabel,
} from '@/types/reviews';
import { useReviews, useReviewStats } from '@/lib/hooks';
import { ReviewStatus as ApiReviewStatus, ReviewCategory as ApiReviewCategory } from '@/lib/api';

export default function ReviewsPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedTab, setSelectedTab] = React.useState<'queue' | 'in-progress' | 'completed'>('queue');
  const [filters, setFilters] = React.useState<ReviewFilters>({});
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = React.useState<'priority' | 'created'>('priority');

  // Map tab to API status
  const getStatusForTab = (): ApiReviewStatus | undefined => {
    switch (selectedTab) {
      case 'queue':
        return 'queued';
      case 'in-progress':
        return 'in_review';
      case 'completed':
        return 'completed';
      default:
        return undefined;
    }
  };

  // Fetch reviews with filters
  const {
    data: reviewsData,
    isLoading: isLoadingReviews,
    isRefetching,
    refetch,
    error: reviewsError,
  } = useReviews({
    status: getStatusForTab(),
    category: filters.category?.[0] as ApiReviewCategory | undefined,
  });

  // Fetch stats
  const {
    data: stats,
    isLoading: isLoadingStats,
    error: statsError,
  } = useReviewStats();

  const isRefreshing = isRefetching;

  // Map API response to UI types
  const reviewItems: ReviewListItem[] = React.useMemo(() => {
    if (!reviewsData?.items) return [];
    return reviewsData.items.map((item) => ({
      id: item.id,
      title: item.title,
      category: item.category as unknown as ReviewCategory,
      status: item.status as unknown as ReviewStatus,
      priority: item.priority as unknown as ReviewPriority,
      created_at: item.created_at,
      engagement_id: '', // Not returned in summary
      assigned_to: item.assigned_to || undefined,
    }));
  }, [reviewsData]);

  // Filter and sort items locally
  const filteredItems = React.useMemo(() => {
    let result = [...reviewItems];

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((item) => item.title.toLowerCase().includes(query));
    }

    // Filter by priority
    if (filters.priority?.length) {
      result = result.filter((item) => filters.priority!.includes(item.priority));
    }

    // Sort
    if (sortBy === 'priority') {
      result.sort((a, b) => {
        if (a.priority !== b.priority) {
          return a.priority - b.priority; // Lower number = higher priority
        }
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      });
    } else {
      result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }

    return result;
  }, [reviewItems, searchQuery, filters, sortBy]);

  // Selection handlers
  const handleSelectItem = (id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === filteredItems.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredItems.map((item) => item.id)));
    }
  };

  // Actions
  const handleStartReview = () => {
    // Get the first queued item by priority
    const nextItem = filteredItems.find((item) => item.status === ReviewStatus.QUEUED);
    if (nextItem) {
      router.push(`/reviews/${nextItem.id}`);
    }
  };

  const handleBulkComplete = async () => {
    console.log('Bulk complete:', Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  const handleRefresh = () => {
    refetch();
  };

  // Stats values
  const queuedCount = stats?.queued ?? 0;
  const inReviewCount = stats?.in_review ?? 0;
  const completedTodayCount = stats?.completed_today ?? 0;
  const avgReviewTime = stats?.avg_review_time_minutes ?? 0;

  // Priority counts are estimated from filtered data when on queue tab
  const criticalCount = selectedTab === 'queue'
    ? filteredItems.filter((item) => item.priority === ReviewPriority.CRITICAL).length
    : 0;
  const highCount = selectedTab === 'queue'
    ? filteredItems.filter((item) => item.priority === ReviewPriority.HIGH).length
    : 0;

  // Loading state
  if (isLoadingReviews && isLoadingStats) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-7xl">
        <div className="flex items-center justify-center h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (reviewsError || statsError) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-7xl">
        <div className="flex flex-col items-center justify-center h-[400px] gap-4">
          <AlertTriangle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Failed to load reviews</h2>
          <p className="text-muted-foreground">
            {(reviewsError as Error)?.message || (statsError as Error)?.message || 'An error occurred'}
          </p>
          <Button onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Review Queue</h1>
          <p className="text-muted-foreground mt-1">
            Review and validate items requiring human attention
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
          </Button>

          <Button onClick={handleStartReview} disabled={queuedCount === 0}>
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Start Reviewing
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              In Queue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoadingStats ? <Loader2 className="h-5 w-5 animate-spin" /> : queuedCount}
            </div>
          </CardContent>
        </Card>
        <Card className={criticalCount > 0 ? 'border-red-500' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              Critical
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn('text-2xl font-bold', criticalCount > 0 && 'text-red-600')}>
              {criticalCount}
            </div>
          </CardContent>
        </Card>
        <Card className={highCount > 0 ? 'border-orange-500' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              High Priority
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn('text-2xl font-bold', highCount > 0 && 'text-orange-600')}>
              {highCount}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              In Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoadingStats ? <Loader2 className="h-5 w-5 animate-spin" /> : inReviewCount}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <BarChart3 className="h-3 w-3" />
              Completed Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {isLoadingStats ? <Loader2 className="h-5 w-5 animate-spin" /> : completedTodayCount}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search review items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={filters.category?.[0] || 'all'}
            onValueChange={(v) =>
              setFilters({
                ...filters,
                category: v === 'all' ? undefined : [v as ReviewCategory],
              })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {Object.values(ReviewCategory).map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {getReviewCategoryLabel(cat)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={sortBy}
            onValueChange={(v) => setSortBy(v as typeof sortBy)}
          >
            <SelectTrigger className="w-[150px]">
              <ListFilter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="priority">By Priority</SelectItem>
              <SelectItem value="created">By Date</SelectItem>
            </SelectContent>
          </Select>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Priority
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              {Object.values(ReviewPriority)
                .filter((p) => typeof p === 'number')
                .map((priority) => (
                  <DropdownMenuCheckboxItem
                    key={priority}
                    checked={filters.priority?.includes(priority as ReviewPriority)}
                    onCheckedChange={(checked) => {
                      const current = filters.priority || [];
                      setFilters({
                        ...filters,
                        priority: checked
                          ? [...current, priority as ReviewPriority]
                          : current.filter((p) => p !== priority),
                      });
                    }}
                  >
                    {getPriorityLabel(priority as ReviewPriority)}
                  </DropdownMenuCheckboxItem>
                ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setFilters({ ...filters, priority: undefined })}>
                Clear priority filter
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        value={selectedTab}
        onValueChange={(v) => setSelectedTab(v as typeof selectedTab)}
        className="mb-6"
      >
        <TabsList>
          <TabsTrigger value="queue" className="relative">
            Queue
            {queuedCount > 0 && (
              <Badge variant="secondary" className="ml-2">
                {queuedCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="in-progress">
            In Progress
            {inReviewCount > 0 && (
              <Badge variant="secondary" className="ml-2">
                {inReviewCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Bulk Actions */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-4 p-4 mb-4 bg-muted rounded-lg">
          <Checkbox
            checked={selectedIds.size === filteredItems.length}
            onCheckedChange={handleSelectAll}
          />
          <span className="text-sm font-medium">
            {selectedIds.size} selected
          </span>
          <div className="flex gap-2 ml-auto">
            <Button size="sm" onClick={handleBulkComplete}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Mark Complete
            </Button>
          </div>
        </div>
      )}

      {/* Review List */}
      <ScrollArea className="h-[calc(100vh-500px)] min-h-[400px]">
        {isLoadingReviews ? (
          <div className="flex items-center justify-center h-[200px]">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <ReviewItemList
            items={filteredItems}
            selectedIds={selectedIds}
            onSelectItem={handleSelectItem}
            showCheckbox={selectedIds.size > 0 || selectedTab === 'queue'}
            emptyMessage={
              searchQuery
                ? 'No items match your search'
                : selectedTab === 'queue'
                ? 'Review queue is empty'
                : 'No items found'
            }
          />
        )}
      </ScrollArea>

      {/* Keyboard shortcuts hint */}
      <div className="mt-4 text-xs text-muted-foreground flex items-center gap-4">
        <span>Keyboard shortcuts:</span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded border bg-muted">N</kbd> Next item
        </span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded border bg-muted">C</kbd> Complete
        </span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded border bg-muted">D</kbd> Defer
        </span>
      </div>
    </div>
  );
}
