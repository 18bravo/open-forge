'use client';

import * as React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { StatusBadge } from '@/components/engagements';
import { cn, formatRelativeTime, formatDateTime } from '@/lib/utils';
import { useApprovals, useApproval, useDecideApproval } from '@/lib/hooks/use-approval';
import type { ApprovalRequest, ApprovalType, ApprovalStatus } from '@/lib/api';
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Clock,
  Database,
  FileText,
  Loader2,
  MessageSquare,
  Settings,
  Shield,
  ThumbsDown,
  ThumbsUp,
  User,
  X,
  XCircle,
} from 'lucide-react';

const approvalTypeIcons: Record<ApprovalType, React.ReactNode> = {
  engagement: <FileText className="h-4 w-4" />,
  tool_execution: <Bot className="h-4 w-4" />,
  data_access: <Database className="h-4 w-4" />,
  schema_change: <Settings className="h-4 w-4" />,
  deployment: <Shield className="h-4 w-4" />,
};

const approvalTypeColors: Record<ApprovalType, string> = {
  engagement: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
  tool_execution: 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
  data_access: 'bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-400',
  schema_change: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900 dark:text-cyan-400',
  deployment: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
};

interface ApprovalsPageProps {
  params: { id: string };
}

export default function ApprovalsPage({ params }: ApprovalsPageProps) {
  const [selectedApprovalId, setSelectedApprovalId] = React.useState<string | null>(null);
  const [filter, setFilter] = React.useState<'all' | 'pending' | 'resolved'>('all');
  const [rejectionReason, setRejectionReason] = React.useState('');

  // Fetch approvals - note: API doesn't support filtering by resource_id yet,
  // so we fetch all and could filter client-side if needed
  const { data: approvalsData, isLoading, error } = useApprovals(
    filter === 'pending' ? { pending_only: true } : undefined
  );
  const { data: selectedApproval, isLoading: detailLoading } = useApproval(selectedApprovalId ?? undefined);
  const decideApprovalMutation = useDecideApproval();

  const approvals = approvalsData?.items ?? [];

  const filteredApprovals = approvals.filter((approval) => {
    if (filter === 'pending') return approval.status === 'pending';
    if (filter === 'resolved') return approval.status !== 'pending';
    return true;
  });

  const pendingCount = approvals.filter((a) => a.status === 'pending').length;

  const handleApprove = async () => {
    if (!selectedApprovalId) return;
    await decideApprovalMutation.mutateAsync({
      id: selectedApprovalId,
      approved: true,
    });
    setSelectedApprovalId(null);
  };

  const handleReject = async () => {
    if (!selectedApprovalId) return;
    await decideApprovalMutation.mutateAsync({
      id: selectedApprovalId,
      approved: false,
      reason: rejectionReason || undefined,
    });
    setSelectedApprovalId(null);
    setRejectionReason('');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="flex flex-col items-center justify-center py-12 text-center">
        <h3 className="text-lg font-medium">Error loading approvals</h3>
        <p className="text-sm text-muted-foreground">
          {error.message || 'Failed to load approvals'}
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Approvals</h2>
          <p className="text-sm text-muted-foreground">
            {pendingCount} pending approval{pendingCount !== 1 ? 's' : ''} for this engagement
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'pending' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('pending')}
          >
            Pending {pendingCount > 0 && `(${pendingCount})`}
          </Button>
          <Button
            variant={filter === 'resolved' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('resolved')}
          >
            Resolved
          </Button>
        </div>
      </div>

      {/* Approval List */}
      <div className="space-y-4">
        {filteredApprovals.length === 0 ? (
          <Card className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle2 className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No approvals</h3>
            <p className="text-sm text-muted-foreground">
              {filter === 'pending'
                ? 'No pending approvals for this engagement.'
                : 'No approvals found for this engagement.'}
            </p>
          </Card>
        ) : (
          filteredApprovals.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              isSelected={selectedApprovalId === approval.id}
              onSelect={() => setSelectedApprovalId(approval.id)}
            />
          ))
        )}
      </div>

      {/* Approval Detail Modal */}
      {selectedApprovalId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            {detailLoading ? (
              <CardContent className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </CardContent>
            ) : selectedApproval ? (
              <>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          'flex h-10 w-10 items-center justify-center rounded-lg',
                          approvalTypeColors[selectedApproval.approval_type]
                        )}
                      >
                        {approvalTypeIcons[selectedApproval.approval_type]}
                      </div>
                      <div>
                        <CardTitle className="text-lg">{selectedApproval.title}</CardTitle>
                        <CardDescription className="capitalize">
                          {selectedApproval.approval_type.replace('_', ' ')}
                        </CardDescription>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setSelectedApprovalId(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm">{selectedApproval.description}</p>

                  {/* Details */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Details</h4>
                    <div className="rounded-lg bg-muted p-3">
                      <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(selectedApproval.details, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="grid gap-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Requested</span>
                      <span>{formatDateTime(selectedApproval.requested_at)}</span>
                    </div>
                    {selectedApproval.expires_at && selectedApproval.status === 'pending' && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Expires</span>
                        <span>{formatRelativeTime(selectedApproval.expires_at)}</span>
                      </div>
                    )}
                    {selectedApproval.approved_by && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Approved by</span>
                        <span>{selectedApproval.approved_by}</span>
                      </div>
                    )}
                    {selectedApproval.rejection_reason && (
                      <div className="pt-2">
                        <span className="text-muted-foreground">Rejection reason</span>
                        <p className="mt-1 text-sm">{selectedApproval.rejection_reason}</p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  {selectedApproval.status === 'pending' && (
                    <div className="space-y-4 pt-4 border-t">
                      <div className="space-y-2">
                        <Label htmlFor="rejection-reason">Rejection Reason (optional)</Label>
                        <Input
                          id="rejection-reason"
                          placeholder="Explain why this request is being rejected..."
                          value={rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          className="flex-1"
                          onClick={handleReject}
                          disabled={decideApprovalMutation.isPending}
                        >
                          {decideApprovalMutation.isPending ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <ThumbsDown className="mr-2 h-4 w-4" />
                          )}
                          Reject
                        </Button>
                        <Button
                          className="flex-1"
                          onClick={handleApprove}
                          disabled={decideApprovalMutation.isPending}
                        >
                          {decideApprovalMutation.isPending ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <ThumbsUp className="mr-2 h-4 w-4" />
                          )}
                          Approve
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </>
            ) : (
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <h3 className="text-lg font-medium">Approval not found</h3>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => setSelectedApprovalId(null)}
                >
                  Close
                </Button>
              </CardContent>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

interface ApprovalCardProps {
  approval: {
    id: string;
    approval_type: ApprovalType;
    status: ApprovalStatus;
    title: string;
    resource_id: string;
    requested_by: string;
    requested_at: string;
    expires_at?: string;
  };
  isSelected: boolean;
  onSelect: () => void;
}

function ApprovalCard({ approval, isSelected, onSelect }: ApprovalCardProps) {
  const isPending = approval.status === 'pending';

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        isPending && 'border-amber-500/50',
        isSelected && 'ring-2 ring-primary'
      )}
      onClick={onSelect}
    >
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg',
              approvalTypeColors[approval.approval_type]
            )}
          >
            {approvalTypeIcons[approval.approval_type]}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-medium">{approval.title}</h3>
              </div>
              <StatusBadge status={approval.status} size="sm" />
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-muted-foreground">
              <span className="capitalize">
                {approval.approval_type.replace('_', ' ')}
              </span>
              <span>{formatRelativeTime(approval.requested_at)}</span>
              {approval.expires_at && isPending && (
                <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                  <Clock className="h-3 w-3" />
                  Expires {formatRelativeTime(approval.expires_at)}
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
