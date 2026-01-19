'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getApprovals,
  getApproval,
  decideApproval,
  type ApprovalRequest,
  type ApprovalRequestSummary,
  type ApprovalType,
  type ApprovalStatus,
  type PaginatedResponse,
} from '@/lib/api';

// Query keys
export const approvalKeys = {
  all: ['approvals'] as const,
  lists: () => [...approvalKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...approvalKeys.lists(), filters] as const,
  pending: () => [...approvalKeys.all, 'pending'] as const,
  details: () => [...approvalKeys.all, 'detail'] as const,
  detail: (id: string) => [...approvalKeys.details(), id] as const,
};

// Fetch approvals list
export function useApprovals(params?: {
  page?: number;
  page_size?: number;
  type?: ApprovalType;
  status?: ApprovalStatus;
  pending_only?: boolean;
}) {
  return useQuery<PaginatedResponse<ApprovalRequestSummary>>({
    queryKey: approvalKeys.list(params ?? {}),
    queryFn: () => getApprovals(params),
  });
}

// Fetch pending approvals (convenience hook)
export function usePendingApprovals(params?: {
  page?: number;
  page_size?: number;
  type?: ApprovalType;
}) {
  return useQuery<PaginatedResponse<ApprovalRequestSummary>>({
    queryKey: approvalKeys.list({ ...params, pending_only: true }),
    queryFn: () => getApprovals({ ...params, pending_only: true }),
    // Poll for new pending approvals
    refetchInterval: 30000, // Every 30 seconds
  });
}

// Fetch single approval
export function useApproval(id: string | undefined) {
  return useQuery<ApprovalRequest>({
    queryKey: approvalKeys.detail(id ?? ''),
    queryFn: () => getApproval(id!),
    enabled: !!id,
  });
}

// Decide on approval (approve or reject)
export function useDecideApproval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      approved,
      reason,
    }: {
      id: string;
      approved: boolean;
      reason?: string;
    }) => decideApproval(id, approved, reason),
    onSuccess: (data, variables) => {
      // Update the cache directly
      queryClient.setQueryData(approvalKeys.detail(variables.id), data);
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: approvalKeys.lists() });
    },
  });
}

// Hook for approval badge count (e.g., for notifications)
export function useApprovalCount() {
  const { data } = usePendingApprovals({ page_size: 1 });
  return data?.total ?? 0;
}
