'use client';

import * as React from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  X,
  Clock,
  SkipForward,
  AlertTriangle,
  User,
  Loader2,
} from 'lucide-react';

import { cn, formatDateTime, formatRelativeTime } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ContextViewer } from '@/components/approvals/ContextViewer';
import { QuickFeedback } from '@/components/approvals/FeedbackForm';
import {
  ReviewStatus,
  ReviewPriority,
  ReviewCategory,
  getReviewStatusColor,
  getPriorityColor,
  getPriorityLabel,
  getReviewCategoryLabel,
} from '@/types/reviews';
import { getInitials } from '@/lib/utils';
import { useReview, useReviews, useCompleteReview, useDeferReview, useSkipReview } from '@/lib/hooks';

export default function ReviewDetailPage() {
  const router = useRouter();
  const params = useParams();
  const itemId = params.id as string;

  const [comments, setComments] = React.useState('');
  const [flags, setFlags] = React.useState<string[]>([]);

  // Fetch the review item
  const {
    data: item,
    isLoading,
    error,
  } = useReview(itemId);

  // Fetch all queued reviews to get navigation info
  const { data: queuedReviews } = useReviews({ status: 'queued' });

  // Mutations
  const completeReviewMutation = useCompleteReview();
  const deferReviewMutation = useDeferReview();
  const skipReviewMutation = useSkipReview();

  const isSubmitting =
    completeReviewMutation.isPending ||
    deferReviewMutation.isPending ||
    skipReviewMutation.isPending;

  // Find next/previous items
  const currentIndex = React.useMemo(() => {
    if (!queuedReviews?.items) return -1;
    return queuedReviews.items.findIndex((r) => r.id === itemId);
  }, [queuedReviews, itemId]);

  const nextItemId = React.useMemo(() => {
    if (!queuedReviews?.items || currentIndex === -1) return null;
    return queuedReviews.items[currentIndex + 1]?.id || null;
  }, [queuedReviews, currentIndex]);

  const previousItemId = React.useMemo(() => {
    if (!queuedReviews?.items || currentIndex <= 0) return null;
    return queuedReviews.items[currentIndex - 1]?.id || null;
  }, [queuedReviews, currentIndex]);

  const totalItems = queuedReviews?.items?.length ?? 0;
  const currentPosition = currentIndex >= 0 ? currentIndex + 1 : 0;

  const handleComplete = async () => {
    try {
      await completeReviewMutation.mutateAsync({
        id: itemId,
        result: { comments, flags },
      });
      if (nextItemId) {
        router.push(`/reviews/${nextItemId}`);
      } else {
        router.push('/reviews');
      }
    } catch (err) {
      console.error('Failed to complete review:', err);
    }
  };

  const handleSkip = async () => {
    try {
      await skipReviewMutation.mutateAsync({
        id: itemId,
        reason: comments || 'Skipped by reviewer',
      });
      if (nextItemId) {
        router.push(`/reviews/${nextItemId}`);
      } else {
        router.push('/reviews');
      }
    } catch (err) {
      console.error('Failed to skip review:', err);
    }
  };

  const handleDefer = async () => {
    try {
      await deferReviewMutation.mutateAsync({
        id: itemId,
        reason: comments || 'Deferred for later',
      });
      router.push('/reviews');
    } catch (err) {
      console.error('Failed to defer review:', err);
    }
  };

  const toggleFlag = (flag: string) => {
    setFlags((prev) =>
      prev.includes(flag) ? prev.filter((f) => f !== flag) : [...prev, flag]
    );
  };

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'c' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        handleComplete();
      } else if (e.key === 'd' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        handleDefer();
      } else if (e.key === 's' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        handleSkip();
      } else if (e.key === 'n' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (nextItemId) {
          router.push(`/reviews/${nextItemId}`);
        }
      } else if (e.key === 'Escape') {
        router.push('/reviews');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router, nextItemId, comments, flags]);

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <div className="flex items-center justify-center h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !item) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <div className="flex flex-col items-center justify-center h-[400px] gap-4">
          <AlertTriangle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Failed to load review</h2>
          <p className="text-muted-foreground">
            {(error as Error)?.message || 'Review item not found'}
          </p>
          <Button onClick={() => router.push('/reviews')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Queue
          </Button>
        </div>
      </div>
    );
  }

  // Map API types to UI types for display
  const priority = item.priority as unknown as ReviewPriority;
  const status = item.status as unknown as ReviewStatus;
  const category = item.category as unknown as ReviewCategory;

  const isCritical = priority === ReviewPriority.CRITICAL;
  const isHigh = priority === ReviewPriority.HIGH;

  return (
    <div className="container mx-auto py-6 px-4 max-w-6xl">
      {/* Navigation header */}
      <div className="flex items-center justify-between mb-6">
        <Link
          href="/reviews"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Queue
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!previousItemId}
            onClick={() => previousItemId && router.push(`/reviews/${previousItemId}`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            {currentPosition > 0 ? `${currentPosition} of ${totalItems}` : '-'}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!nextItemId}
            onClick={() => nextItemId && router.push(`/reviews/${nextItemId}`)}
          >
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Badge
            variant="secondary"
            className={getReviewStatusColor(status)}
          >
            {item.status.replace('_', ' ')}
          </Badge>
          <Badge
            variant="outline"
            className={getPriorityColor(priority)}
          >
            {getPriorityLabel(priority)}
          </Badge>
          <Badge variant="outline">
            {getReviewCategoryLabel(category)}
          </Badge>
          {isCritical && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              Critical
            </Badge>
          )}
        </div>

        <h1 className="text-2xl font-bold mb-2">{item.title}</h1>

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            Created {formatRelativeTime(item.created_at)}
          </span>
          {item.assigned_to && (
            <span className="flex items-center gap-1">
              <User className="h-4 w-4" />
              Assigned to {item.assigned_to}
            </span>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column - Content to review */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle>Description</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{item.description}</p>
              </div>
            </CardContent>
          </Card>

          {/* Review Data */}
          {item.context_data && Object.keys(item.context_data).length > 0 && (
            <ContextViewer
              data={item.context_data}
              title="Review Data"
              maxHeight="500px"
            />
          )}

          {/* Quick Feedback */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Feedback</CardTitle>
              <CardDescription>
                Rate the quality of this detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <QuickFeedback
                sourceType="review_item"
                sourceId={item.id}
                onSubmit={async (data) => {
                  console.log('Feedback submitted:', data);
                }}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right column - Actions */}
        <div className="space-y-6">
          {/* Review Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Review Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Flags */}
              <div>
                <Label className="text-sm">Flags</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {['Data Issue', 'Follow-up Required', 'Source Problem', 'False Positive'].map(
                    (flag) => (
                      <Badge
                        key={flag}
                        variant={flags.includes(flag) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => toggleFlag(flag)}
                      >
                        {flag}
                      </Badge>
                    )
                  )}
                </div>
              </div>

              <Separator />

              {/* Comments */}
              <div>
                <Label htmlFor="review-comments">Comments (optional)</Label>
                <Textarea
                  id="review-comments"
                  placeholder="Add notes about this review..."
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  rows={4}
                  className="mt-2"
                />
              </div>

              <Separator />

              {/* Action buttons */}
              <div className="space-y-2">
                <Button
                  className="w-full bg-green-600 hover:bg-green-700"
                  onClick={handleComplete}
                  disabled={isSubmitting}
                >
                  {completeReviewMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4 mr-2" />
                  )}
                  Complete Review
                  <kbd className="ml-auto px-1.5 py-0.5 rounded border bg-green-700 text-[10px]">C</kbd>
                </Button>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleDefer}
                  disabled={isSubmitting}
                >
                  {deferReviewMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Clock className="h-4 w-4 mr-2" />
                  )}
                  Defer for Later
                  <kbd className="ml-auto px-1.5 py-0.5 rounded border bg-muted text-[10px]">D</kbd>
                </Button>

                <Button
                  variant="ghost"
                  className="w-full"
                  onClick={handleSkip}
                  disabled={isSubmitting}
                >
                  {skipReviewMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <SkipForward className="h-4 w-4 mr-2" />
                  )}
                  Skip
                  <kbd className="ml-auto px-1.5 py-0.5 rounded border bg-muted text-[10px]">S</kbd>
                </Button>
              </div>

              {/* Error display */}
              {(completeReviewMutation.error || deferReviewMutation.error || skipReviewMutation.error) && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <p className="text-sm text-destructive">
                    {(completeReviewMutation.error as Error)?.message ||
                      (deferReviewMutation.error as Error)?.message ||
                      (skipReviewMutation.error as Error)?.message ||
                      'An error occurred'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Item Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Item Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="text-muted-foreground">ID</p>
                <p className="font-mono">{item.id}</p>
              </div>

              <Separator />

              <div>
                <p className="text-muted-foreground">Created At</p>
                <p>{formatDateTime(item.created_at)}</p>
              </div>

              <Separator />

              <div>
                <p className="text-muted-foreground">Created By</p>
                <p>{item.created_by}</p>
              </div>

              {item.engagement_id && (
                <>
                  <Separator />
                  <div>
                    <p className="text-muted-foreground">Engagement</p>
                    <Link
                      href={`/engagements/${item.engagement_id}`}
                      className="text-primary hover:underline"
                    >
                      {item.engagement_id}
                    </Link>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Keyboard Shortcuts */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Keyboard Shortcuts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Complete</span>
                <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">C</kbd>
              </div>
              <div className="flex justify-between">
                <span>Defer</span>
                <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">D</kbd>
              </div>
              <div className="flex justify-between">
                <span>Skip</span>
                <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">S</kbd>
              </div>
              <div className="flex justify-between">
                <span>Next Item</span>
                <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">N</kbd>
              </div>
              <div className="flex justify-between">
                <span>Go Back</span>
                <kbd className="px-2 py-0.5 rounded border bg-muted font-mono text-xs">Esc</kbd>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
