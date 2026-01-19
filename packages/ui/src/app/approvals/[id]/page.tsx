'use client';

import * as React from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Clock,
  User,
  Bot,
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  Loader2,
} from 'lucide-react';

import { cn, formatDateTime, formatRelativeTime } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  ApprovalActions,
  ApprovalTimeline,
  ContextViewer,
  DiffViewer,
  type TimelineEvent,
} from '@/components/approvals';
import {
  ApprovalRequest,
  ApprovalType,
  ApprovalStatus,
  getApprovalStatusColor,
  getApprovalTypeLabel,
  isUrgent,
  isExpiringSoon,
} from '@/types/approvals';
import { getInitials } from '@/lib/utils';
import { useApproval, useDecideApproval } from '@/lib/hooks/use-approval';

// TODO: Timeline endpoint doesn't exist yet - using empty array
const emptyTimeline: TimelineEvent[] = [];

export default function ApprovalDetailPage() {
  const router = useRouter();
  const params = useParams();
  const approvalId = params.id as string;
  const [copied, setCopied] = React.useState(false);

  // Fetch approval data from API
  const { data: approval, isLoading, isError, refetch } = useApproval(approvalId);
  const decideApproval = useDecideApproval();

  // TODO: Fetch timeline from API when endpoint is available
  const timeline = emptyTimeline;

  const handleApprove = async (comments?: string) => {
    await decideApproval.mutateAsync({ id: approvalId, approved: true, reason: comments });
    router.push('/approvals');
  };

  const handleReject = async (comments: string) => {
    await decideApproval.mutateAsync({ id: approvalId, approved: false, reason: comments });
    router.push('/approvals');
  };

  const handleRequestChanges = async (comments: string) => {
    // TODO: Implement request changes API when available
    console.log('Request changes:', approvalId, 'Comments:', comments);
  };

  const handleCopyId = async () => {
    if (!approval) return;
    await navigator.clipboard.writeText(approval.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'Escape') {
        router.push('/approvals');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router]);

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <Link
          href="/approvals"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Approvals
        </Link>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !approval) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <Link
          href="/approvals"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Approvals
        </Link>
        <div className="text-center py-24">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium">Approval not found</p>
          <p className="text-sm text-muted-foreground mb-4">
            The approval request could not be loaded.
          </p>
          <Button variant="outline" onClick={() => refetch()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  const urgent = isUrgent(approval);
  const expiringSoon = isExpiringSoon(approval);
  const isAgent = approval.requested_by.includes('Agent');
  const isPending = approval.status === ApprovalStatus.PENDING || approval.status === ApprovalStatus.ESCALATED;
  const isMutating = decideApproval.isPending;

  return (
    <div className="container mx-auto py-6 px-4 max-w-6xl">
      {/* Back button and header */}
      <div className="mb-6">
        <Link
          href="/approvals"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Approvals
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge
                variant="secondary"
                className={getApprovalStatusColor(approval.status)}
              >
                {approval.status}
              </Badge>
              <Badge variant="outline">
                {getApprovalTypeLabel(approval.approval_type)}
              </Badge>
              {approval.escalation_level !== 'level_1' && (
                <Badge variant="outline" className="bg-orange-50 dark:bg-orange-900/20">
                  Escalated: {approval.escalation_level}
                </Badge>
              )}
              {urgent && (
                <Badge variant="destructive" className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Urgent
                </Badge>
              )}
            </div>

            <h1 className="text-2xl font-bold mb-2">{approval.title}</h1>

            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <button
                onClick={handleCopyId}
                className="flex items-center gap-1 hover:text-foreground"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-green-500" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
                <span className="font-mono">{approval.id}</span>
              </button>

              <span className="flex items-center gap-1">
                {isAgent ? (
                  <Bot className="h-4 w-4" />
                ) : (
                  <User className="h-4 w-4" />
                )}
                {approval.requested_by}
              </span>

              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatRelativeTime(approval.requested_at)}
              </span>
            </div>
          </div>

          {/* Actions */}
          {isPending && (
            <div className="relative">
              {isMutating && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded-lg z-10">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              )}
              <ApprovalActions
                approvalId={approval.id}
                onApprove={handleApprove}
                onReject={handleReject}
                onRequestChanges={handleRequestChanges}
              />
            </div>
          )}
        </div>
      </div>

      {/* Deadline warning */}
      {approval.deadline && isPending && (
        <div
          className={cn(
            'rounded-lg border p-4 mb-6 flex items-center gap-3',
            urgent
              ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
              : expiringSoon
              ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
              : 'border-muted'
          )}
        >
          <Clock
            className={cn(
              'h-5 w-5',
              urgent
                ? 'text-red-600 dark:text-red-400'
                : expiringSoon
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-muted-foreground'
            )}
          />
          <div>
            <p className="font-medium">
              {urgent ? 'Action required urgently' : 'Deadline approaching'}
            </p>
            <p className="text-sm text-muted-foreground">
              This request expires {formatRelativeTime(approval.deadline)} (
              {formatDateTime(approval.deadline)})
            </p>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle>Description</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{approval.description}</p>
              </div>
            </CardContent>
          </Card>

          {/* Tabs for different views */}
          <Tabs defaultValue="context">
            <TabsList>
              <TabsTrigger value="context">Context</TabsTrigger>
              <TabsTrigger value="changes">Changes</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
            </TabsList>

            <TabsContent value="context" className="mt-4">
              {approval.context_data ? (
                <ContextViewer
                  data={approval.context_data}
                  title="Request Context"
                  maxHeight="500px"
                />
              ) : (
                <Card>
                  <CardContent className="py-8 text-center text-muted-foreground">
                    No additional context provided
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="changes" className="mt-4">
              {approval.context_data?.before && approval.context_data?.after ? (
                <DiffViewer
                  before={approval.context_data.before}
                  after={approval.context_data.after}
                  title="Configuration Changes"
                  maxHeight="500px"
                />
              ) : (
                <Card>
                  <CardContent className="py-8 text-center text-muted-foreground">
                    No changes to display
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="timeline" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  {timeline.length > 0 ? (
                    <ApprovalTimeline events={timeline} />
                  ) : (
                    <p className="text-center text-muted-foreground py-4">
                      No activity recorded yet
                    </p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right column - Metadata */}
        <div className="space-y-6">
          {/* Request Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Request Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Requester</p>
                <div className="flex items-center gap-2 mt-1">
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-xs">
                      {isAgent ? <Bot className="h-3 w-3" /> : getInitials(approval.requested_by)}
                    </AvatarFallback>
                  </Avatar>
                  <span className="font-medium">{approval.requested_by}</span>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm text-muted-foreground">Requested At</p>
                <p className="font-medium">{formatDateTime(approval.requested_at)}</p>
              </div>

              {approval.deadline && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm text-muted-foreground">Deadline</p>
                    <p
                      className={cn(
                        'font-medium',
                        urgent && 'text-red-600 dark:text-red-400'
                      )}
                    >
                      {formatDateTime(approval.deadline)}
                    </p>
                  </div>
                </>
              )}

              <Separator />

              <div>
                <p className="text-sm text-muted-foreground">Engagement</p>
                <Link
                  href={`/engagements/${approval.engagement_id}`}
                  className="font-medium text-primary hover:underline inline-flex items-center gap-1"
                >
                  {approval.engagement_id}
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </div>

              {approval.details?.risk_level && (
                <>
                  <Separator />
                  <div>
                    <p className="text-sm text-muted-foreground">Risk Level</p>
                    <Badge
                      variant="outline"
                      className={cn(
                        approval.details.risk_level === 'high' &&
                          'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400',
                        approval.details.risk_level === 'medium' &&
                          'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
                        approval.details.risk_level === 'low' &&
                          'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                      )}
                    >
                      {(approval.details.risk_level as string).toUpperCase()}
                    </Badge>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Decision Info (if decided) */}
          {approval.decided_by && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Decision</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Decided By</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback className="text-xs">
                        {getInitials(approval.decided_by)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="font-medium">{approval.decided_by}</span>
                  </div>
                </div>

                {approval.decided_at && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-sm text-muted-foreground">Decided At</p>
                      <p className="font-medium">{formatDateTime(approval.decided_at)}</p>
                    </div>
                  </>
                )}

                {approval.decision_comments && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-sm text-muted-foreground">Comments</p>
                      <p className="mt-1">{approval.decision_comments}</p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          {isPending && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Quick Actions</CardTitle>
                <CardDescription>Keyboard shortcuts available</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Approve</span>
                  <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">A</kbd>
                </div>
                <div className="flex justify-between">
                  <span>Reject</span>
                  <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">R</kbd>
                </div>
                <div className="flex justify-between">
                  <span>Request Changes</span>
                  <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">C</kbd>
                </div>
                <div className="flex justify-between">
                  <span>Go Back</span>
                  <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">Esc</kbd>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
