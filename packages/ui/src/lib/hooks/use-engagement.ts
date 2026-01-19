'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getEngagements,
  getEngagement,
  createEngagement,
  updateEngagement,
  updateEngagementStatus,
  type Engagement,
  type EngagementCreate,
  type EngagementStatus,
  type EngagementPriority,
  type PaginatedResponse,
  type EngagementSummary,
} from '@/lib/api';

// Query keys
export const engagementKeys = {
  all: ['engagements'] as const,
  lists: () => [...engagementKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...engagementKeys.lists(), filters] as const,
  details: () => [...engagementKeys.all, 'detail'] as const,
  detail: (id: string) => [...engagementKeys.details(), id] as const,
};

// Fetch engagements list
export function useEngagements(params?: {
  page?: number;
  page_size?: number;
  status?: EngagementStatus;
  priority?: EngagementPriority;
  search?: string;
}) {
  return useQuery<PaginatedResponse<EngagementSummary>>({
    queryKey: engagementKeys.list(params ?? {}),
    queryFn: () => getEngagements(params),
  });
}

// Fetch single engagement
export function useEngagement(id: string | undefined) {
  return useQuery<Engagement>({
    queryKey: engagementKeys.detail(id ?? ''),
    queryFn: () => getEngagement(id!),
    enabled: !!id,
  });
}

// Create engagement mutation
export function useCreateEngagement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EngagementCreate) => createEngagement(data),
    onSuccess: () => {
      // Invalidate and refetch engagements list
      queryClient.invalidateQueries({ queryKey: engagementKeys.lists() });
    },
  });
}

// Update engagement mutation
export function useUpdateEngagement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EngagementCreate> }) =>
      updateEngagement(id, data),
    onSuccess: (data, variables) => {
      // Update the cache directly
      queryClient.setQueryData(engagementKeys.detail(variables.id), data);
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: engagementKeys.lists() });
    },
  });
}

// Update engagement status mutation
export function useUpdateEngagementStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      status,
      reason,
    }: {
      id: string;
      status: EngagementStatus;
      reason?: string;
    }) => updateEngagementStatus(id, status, reason),
    onSuccess: (data, variables) => {
      // Update the cache directly
      queryClient.setQueryData(engagementKeys.detail(variables.id), data);
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: engagementKeys.lists() });
    },
  });
}
