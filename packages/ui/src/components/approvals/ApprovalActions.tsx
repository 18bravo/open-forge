'use client';

import * as React from 'react';
import { Check, X, MessageSquare, ArrowUpRight, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';

interface ApprovalActionsProps {
  approvalId: string;
  onApprove: (comments?: string) => Promise<void>;
  onReject: (comments: string) => Promise<void>;
  onRequestChanges: (comments: string) => Promise<void>;
  disabled?: boolean;
  className?: string;
}

export function ApprovalActions({
  approvalId,
  onApprove,
  onReject,
  onRequestChanges,
  disabled = false,
  className,
}: ApprovalActionsProps) {
  const [isApproving, setIsApproving] = React.useState(false);
  const [isRejecting, setIsRejecting] = React.useState(false);
  const [isRequestingChanges, setIsRequestingChanges] = React.useState(false);
  const [approveDialogOpen, setApproveDialogOpen] = React.useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = React.useState(false);
  const [changesDialogOpen, setChangesDialogOpen] = React.useState(false);
  const [comments, setComments] = React.useState('');

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await onApprove(comments || undefined);
      setApproveDialogOpen(false);
      setComments('');
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!comments.trim()) return;
    setIsRejecting(true);
    try {
      await onReject(comments);
      setRejectDialogOpen(false);
      setComments('');
    } finally {
      setIsRejecting(false);
    }
  };

  const handleRequestChanges = async () => {
    if (!comments.trim()) return;
    setIsRequestingChanges(true);
    try {
      await onRequestChanges(comments);
      setChangesDialogOpen(false);
      setComments('');
    } finally {
      setIsRequestingChanges(false);
    }
  };

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if not in an input/textarea and no dialog is open
      if (
        disabled ||
        approveDialogOpen ||
        rejectDialogOpen ||
        changesDialogOpen ||
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      if (e.key === 'a' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setApproveDialogOpen(true);
      } else if (e.key === 'r' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setRejectDialogOpen(true);
      } else if (e.key === 'c' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setChangesDialogOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [disabled, approveDialogOpen, rejectDialogOpen, changesDialogOpen]);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Approve Button */}
      <Dialog open={approveDialogOpen} onOpenChange={setApproveDialogOpen}>
        <DialogTrigger asChild>
          <Button
            variant="default"
            disabled={disabled}
            className="bg-green-600 hover:bg-green-700"
          >
            <Check className="mr-2 h-4 w-4" />
            Approve
            <kbd className="ml-2 pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex">
              A
            </kbd>
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Request</DialogTitle>
            <DialogDescription>
              Approve this request. You can optionally add comments.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="approve-comments">Comments (optional)</Label>
              <Textarea
                id="approve-comments"
                placeholder="Add any comments..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setApproveDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleApprove}
              disabled={isApproving}
              className="bg-green-600 hover:bg-green-700"
            >
              {isApproving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Check className="mr-2 h-4 w-4" />
              )}
              Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Button */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="destructive" disabled={disabled}>
            <X className="mr-2 h-4 w-4" />
            Reject
            <kbd className="ml-2 pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex">
              R
            </kbd>
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Request</DialogTitle>
            <DialogDescription>
              Reject this request. Please provide a reason.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="reject-comments">
                Reason <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="reject-comments"
                placeholder="Explain why this request is being rejected..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={3}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRejectDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={isRejecting || !comments.trim()}
            >
              {isRejecting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <X className="mr-2 h-4 w-4" />
              )}
              Reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Request Changes Button */}
      <Dialog open={changesDialogOpen} onOpenChange={setChangesDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" disabled={disabled}>
            <MessageSquare className="mr-2 h-4 w-4" />
            Request Changes
            <kbd className="ml-2 pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex">
              C
            </kbd>
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Changes</DialogTitle>
            <DialogDescription>
              Request modifications before approval. Describe what changes are needed.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="changes-comments">
                Required Changes <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="changes-comments"
                placeholder="Describe what changes are needed..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={4}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setChangesDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRequestChanges}
              disabled={isRequestingChanges || !comments.trim()}
            >
              {isRequestingChanges ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <ArrowUpRight className="mr-2 h-4 w-4" />
              )}
              Request Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Compact version for inline use
export function ApprovalActionsCompact({
  onApprove,
  onReject,
  disabled = false,
  className,
}: {
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
  disabled?: boolean;
  className?: string;
}) {
  const [isApproving, setIsApproving] = React.useState(false);
  const [isRejecting, setIsRejecting] = React.useState(false);

  const handleApprove = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsApproving(true);
    try {
      await onApprove();
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsRejecting(true);
    try {
      await onReject();
    } finally {
      setIsRejecting(false);
    }
  };

  return (
    <div className={cn('flex items-center gap-1', className)}>
      <Button
        variant="ghost"
        size="sm"
        disabled={disabled || isApproving}
        onClick={handleApprove}
        className="h-8 w-8 p-0 text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20"
      >
        {isApproving ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Check className="h-4 w-4" />
        )}
        <span className="sr-only">Approve</span>
      </Button>
      <Button
        variant="ghost"
        size="sm"
        disabled={disabled || isRejecting}
        onClick={handleReject}
        className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
      >
        {isRejecting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <X className="h-4 w-4" />
        )}
        <span className="sr-only">Reject</span>
      </Button>
    </div>
  );
}
