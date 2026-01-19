'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Filter,
  Bell,
  BellRing,
  CheckCircle2,
  XCircle,
  ArrowUpRight,
  RefreshCw,
  Volume2,
  VolumeX,
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
import { ApprovalCard } from '@/components/approvals/ApprovalCard';
import {
  ApprovalListItem,
  ApprovalType,
  ApprovalStatus,
  ApprovalFilters,
  ApprovalStats,
  getApprovalTypeLabel,
  isUrgent,
} from '@/types/approvals';
import {
  useApprovals,
  usePendingApprovals,
  useDecideApproval,
} from '@/lib/hooks/use-approval';

export default function ApprovalsPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedTab, setSelectedTab] = React.useState<'pending' | 'all' | 'my-requests'>('pending');
  const [filters, setFilters] = React.useState<ApprovalFilters>({});
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set());
  const [soundEnabled, setSoundEnabled] = React.useState(false);

  // API hooks
  const pendingQuery = usePendingApprovals({ page_size: 50 });
  const allQuery = useApprovals({
    page_size: 50,
    status: filters.status?.[0] as ApprovalStatus | undefined
  });
  const currentQuery = selectedTab === 'pending' ? pendingQuery : allQuery;
  const { data, isLoading, isError, refetch } = currentQuery;

  const decideApproval = useDecideApproval();

  // Extract approvals from paginated response
  const approvals = React.useMemo(() => {
    return (data?.items ?? []) as ApprovalListItem[];
  }, [data]);

  // Compute stats from real data
  const stats = React.useMemo(() => {
    const pendingApprovals = pendingQuery.data?.items ?? [];
    const allApprovals = approvals;

    const totalPending = pendingQuery.data?.total ?? 0;
    const urgentCount = pendingApprovals.filter(a => isUrgent(a as ApprovalListItem)).length;
    const expiringSoonCount = pendingApprovals.filter(a => {
      const item = a as ApprovalListItem;
      if (!item.deadline) return false;
      const deadline = new Date(item.deadline);
      const now = new Date();
      const hoursUntilDeadline = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60);
      return hoursUntilDeadline > 0 && hoursUntilDeadline <= 24;
    }).length;

    // Count by type
    const byType = Object.values(ApprovalType).reduce((acc, type) => {
      acc[type] = pendingApprovals.filter(a => a.approval_type === type).length;
      return acc;
    }, {} as Record<ApprovalType, number>);

    // Count by status
    const byStatus = Object.values(ApprovalStatus).reduce((acc, status) => {
      acc[status] = allApprovals.filter(a => a.status === status).length;
      return acc;
    }, {} as Record<ApprovalStatus, number>);

    return {
      total_pending: totalPending,
      urgent_count: urgentCount,
      expiring_soon: expiringSoonCount,
      by_type: byType,
      by_status: byStatus,
    } as ApprovalStats;
  }, [pendingQuery.data, approvals]);

  // Filter approvals
  const filteredApprovals = React.useMemo(() => {
    let result = [...approvals];

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.title.toLowerCase().includes(query) ||
          a.requested_by.toLowerCase().includes(query)
      );
    }

    // Filter by type
    if (filters.type?.length) {
      result = result.filter((a) => filters.type!.includes(a.approval_type));
    }

    // Filter by status (for non-pending tab)
    if (selectedTab !== 'pending' && filters.status?.length) {
      result = result.filter((a) => filters.status!.includes(a.status));
    }

    // Sort: urgent first, then by date
    result.sort((a, b) => {
      const aUrgent = isUrgent(a);
      const bUrgent = isUrgent(b);
      if (aUrgent && !bUrgent) return -1;
      if (!aUrgent && bUrgent) return 1;
      return new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime();
    });

    return result;
  }, [approvals, searchQuery, selectedTab, filters]);

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
    if (selectedIds.size === filteredApprovals.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredApprovals.map((a) => a.id)));
    }
  };

  // Action handlers
  const handleApprove = async (id: string) => {
    await decideApproval.mutateAsync({ id, approved: true });
  };

  const handleReject = async (id: string, reason: string) => {
    await decideApproval.mutateAsync({ id, approved: false, reason });
  };

  // Bulk actions
  const handleBulkApprove = async () => {
    const ids = Array.from(selectedIds);
    for (const id of ids) {
      await decideApproval.mutateAsync({ id, approved: true });
    }
    setSelectedIds(new Set());
  };

  const handleBulkReject = async () => {
    const ids = Array.from(selectedIds);
    for (const id of ids) {
      await decideApproval.mutateAsync({ id, approved: false, reason: 'Bulk rejection' });
    }
    setSelectedIds(new Set());
  };

  const handleRefresh = async () => {
    await refetch();
  };

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'n' && !e.metaKey && !e.ctrlKey) {
        // Navigate to next approval
        const currentIndex = filteredApprovals.findIndex((a) => selectedIds.has(a.id));
        const nextIndex = currentIndex < filteredApprovals.length - 1 ? currentIndex + 1 : 0;
        if (filteredApprovals[nextIndex]) {
          router.push(`/approvals/${filteredApprovals[nextIndex].id}`);
        }
      } else if (e.key === 'r' && !e.metaKey && !e.ctrlKey) {
        handleRefresh();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredApprovals, selectedIds, router]);

  const urgentCount = filteredApprovals.filter(isUrgent).length;
  const isRefreshing = currentQuery.isFetching;
  const isMutating = decideApproval.isPending;

  return (
    <div className="container mx-auto py-6 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Approvals</h1>
          <p className="text-muted-foreground mt-1">
            Review and approve pending requests
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Notification toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSoundEnabled(!soundEnabled)}
            title={soundEnabled ? 'Disable sound notifications' : 'Enable sound notifications'}
          >
            {soundEnabled ? (
              <Volume2 className="h-5 w-5" />
            ) : (
              <VolumeX className="h-5 w-5" />
            )}
          </Button>

          {/* Refresh */}
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
          </Button>

          {/* Notification badge */}
          <Button variant="outline" className="relative">
            <BellRing className="h-4 w-4 mr-2" />
            Notifications
            {urgentCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center text-xs"
              >
                {urgentCount}
              </Badge>
            )}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats.total_pending}
            </div>
          </CardContent>
        </Card>
        <Card className={urgentCount > 0 ? 'border-red-500' : ''}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Urgent
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn('text-2xl font-bold', urgentCount > 0 && 'text-red-600')}>
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats.urgent_count}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Expiring Soon
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats.expiring_soon}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Agent Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats.by_type[ApprovalType.AGENT_ACTION]}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search approvals..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={filters.type?.[0] || 'all'}
            onValueChange={(v) => setFilters({ ...filters, type: v === 'all' ? undefined : [v as ApprovalType] })}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {Object.values(ApprovalType).map((type) => (
                <SelectItem key={type} value={type}>
                  {getApprovalTypeLabel(type)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="p-2">
                <p className="text-sm font-medium mb-2">Status</p>
                {Object.values(ApprovalStatus).map((status) => (
                  <DropdownMenuCheckboxItem
                    key={status}
                    checked={filters.status?.includes(status)}
                    onCheckedChange={(checked) => {
                      const current = filters.status || [];
                      setFilters({
                        ...filters,
                        status: checked
                          ? [...current, status]
                          : current.filter((s) => s !== status),
                      });
                    }}
                  >
                    {status}
                  </DropdownMenuCheckboxItem>
                ))}
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setFilters({})}>
                Clear filters
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
          <TabsTrigger value="pending" className="relative">
            Pending
            {stats.total_pending > 0 && (
              <Badge variant="secondary" className="ml-2">
                {stats.total_pending}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="my-requests">My Requests</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Bulk Actions */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-4 p-4 mb-4 bg-muted rounded-lg">
          <Checkbox
            checked={selectedIds.size === filteredApprovals.length}
            onCheckedChange={handleSelectAll}
          />
          <span className="text-sm font-medium">
            {selectedIds.size} selected
          </span>
          <div className="flex gap-2 ml-auto">
            <Button
              size="sm"
              onClick={handleBulkApprove}
              className="bg-green-600 hover:bg-green-700"
              disabled={isMutating}
            >
              {isMutating ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Approve All
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={handleBulkReject}
              disabled={isMutating}
            >
              {isMutating ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <XCircle className="h-4 w-4 mr-2" />
              )}
              Reject All
            </Button>
          </div>
        </div>
      )}

      {/* Approval List */}
      <ScrollArea className="h-[calc(100vh-450px)] min-h-[400px]">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : isError ? (
          <div className="text-center py-12 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Failed to load approvals</p>
            <p className="text-sm mb-4">
              There was an error loading the approvals. Please try again.
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        ) : filteredApprovals.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">No approvals found</p>
            <p className="text-sm">
              {searchQuery
                ? 'Try adjusting your search or filters'
                : 'All caught up! Check back later.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredApprovals.map((approval) => (
              <ApprovalCard
                key={approval.id}
                approval={approval}
                selected={selectedIds.has(approval.id)}
                onSelect={handleSelectItem}
                showCheckbox={selectedIds.size > 0 || selectedTab === 'pending'}
              />
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Keyboard shortcuts hint */}
      <div className="mt-4 text-xs text-muted-foreground flex items-center gap-4">
        <span>Keyboard shortcuts:</span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded border bg-muted">A</kbd> Approve
        </span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded border bg-muted">R</kbd> Reject / Refresh
        </span>
        <span>
          <kbd className="px-1.5 py-0.5 rounded border bg-muted">N</kbd> Next
        </span>
      </div>
    </div>
  );
}
