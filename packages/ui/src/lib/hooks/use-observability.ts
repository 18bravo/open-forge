'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getEngagementTraces,
  getAgentTraces,
  getObservabilityStats,
  submitFeedback,
  getTrace,
  getDashboardUrl,
  getLangSmithHealth,
  type TraceInfo,
  type ObservabilityStats,
  type FeedbackCreate,
  type FeedbackResponse,
  type DashboardUrlResponse,
  type LangSmithHealth,
  type PaginatedResponse,
} from '@/lib/api';

// ============================================================================
// Query Keys
// ============================================================================

export const observabilityKeys = {
  all: ['observability'] as const,
  traces: () => [...observabilityKeys.all, 'traces'] as const,
  engagementTraces: (engagementId: string, filters: Record<string, unknown>) =>
    [...observabilityKeys.traces(), 'engagement', engagementId, filters] as const,
  agentTraces: (agentId: string, filters: Record<string, unknown>) =>
    [...observabilityKeys.traces(), 'agent', agentId, filters] as const,
  trace: (runId: string) => [...observabilityKeys.traces(), runId] as const,
  stats: (filters: Record<string, unknown>) =>
    [...observabilityKeys.all, 'stats', filters] as const,
  dashboardUrl: (params: Record<string, unknown>) =>
    [...observabilityKeys.all, 'dashboard-url', params] as const,
  health: () => [...observabilityKeys.all, 'health'] as const,
};

// ============================================================================
// Engagement Traces Hook
// ============================================================================

export interface UseEngagementTracesParams {
  page?: number;
  page_size?: number;
  status?: 'success' | 'error' | 'running';
  start_time?: string;
  end_time?: string;
}

/**
 * Hook to fetch traces for a specific engagement.
 *
 * @param engagementId - The engagement ID to fetch traces for
 * @param params - Optional pagination and filter parameters
 * @returns Query result with paginated traces
 *
 * @example
 * const { data, isLoading, error } = useEngagementTraces('eng-123', { page: 1 });
 */
export function useEngagementTraces(
  engagementId: string | undefined,
  params?: UseEngagementTracesParams
) {
  return useQuery<PaginatedResponse<TraceInfo>>({
    queryKey: observabilityKeys.engagementTraces(engagementId ?? '', params ?? {}),
    queryFn: () => getEngagementTraces(engagementId!, params),
    enabled: !!engagementId,
    // Traces can change frequently during active engagements
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: (query) => {
      // Poll more frequently if there are running traces
      const data = query.state.data as PaginatedResponse<TraceInfo> | undefined;
      const hasRunning = data?.items.some((t) => t.status === 'running');
      return hasRunning ? 5000 : 30000;
    },
  });
}

// ============================================================================
// Agent Traces Hook
// ============================================================================

export interface UseAgentTracesParams {
  page?: number;
  page_size?: number;
  engagement_id?: string;
  start_time?: string;
  end_time?: string;
}

/**
 * Hook to fetch traces for a specific agent.
 *
 * @param agentId - The agent ID to fetch traces for
 * @param params - Optional pagination and filter parameters
 * @returns Query result with paginated traces
 *
 * @example
 * const { data, isLoading } = useAgentTraces('agent-discovery-001');
 */
export function useAgentTraces(
  agentId: string | undefined,
  params?: UseAgentTracesParams
) {
  return useQuery<PaginatedResponse<TraceInfo>>({
    queryKey: observabilityKeys.agentTraces(agentId ?? '', params ?? {}),
    queryFn: () => getAgentTraces(agentId!, params),
    enabled: !!agentId,
    staleTime: 30 * 1000,
  });
}

// ============================================================================
// Single Trace Hook
// ============================================================================

/**
 * Hook to fetch a single trace by run ID.
 *
 * @param runId - The run ID to fetch
 * @returns Query result with trace details
 *
 * @example
 * const { data: trace } = useTrace('run-123');
 */
export function useTrace(runId: string | undefined) {
  return useQuery<TraceInfo>({
    queryKey: observabilityKeys.trace(runId ?? ''),
    queryFn: () => getTrace(runId!),
    enabled: !!runId,
    staleTime: 60 * 1000, // 1 minute - single traces don't change often
  });
}

// ============================================================================
// Observability Stats Hook
// ============================================================================

export interface UseObservabilityStatsParams {
  engagement_id?: string;
  start_time?: string;
  end_time?: string;
}

/**
 * Hook to fetch aggregated observability statistics.
 *
 * @param params - Optional filter parameters
 * @returns Query result with statistics
 *
 * @example
 * const { data: stats } = useObservabilityStats({ engagement_id: 'eng-123' });
 */
export function useObservabilityStats(params?: UseObservabilityStatsParams) {
  return useQuery<ObservabilityStats>({
    queryKey: observabilityKeys.stats(params ?? {}),
    queryFn: () => getObservabilityStats(params),
    staleTime: 60 * 1000, // 1 minute
    // Refresh stats periodically
    refetchInterval: 60 * 1000,
  });
}

// ============================================================================
// Submit Feedback Mutation
// ============================================================================

/**
 * Hook to submit feedback for a trace run.
 *
 * @returns Mutation for submitting feedback
 *
 * @example
 * const submitFeedback = useSubmitFeedback();
 *
 * submitFeedback.mutate({
 *   run_id: 'run-123',
 *   score: 0.8,
 *   comment: 'Good response',
 * });
 */
export function useSubmitFeedback() {
  const queryClient = useQueryClient();

  return useMutation<FeedbackResponse, Error, FeedbackCreate>({
    mutationFn: (data: FeedbackCreate) => submitFeedback(data),
    onSuccess: (_, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: observabilityKeys.trace(variables.run_id),
      });
      queryClient.invalidateQueries({
        queryKey: observabilityKeys.stats({}),
      });
    },
  });
}

// ============================================================================
// Dashboard URL Hook
// ============================================================================

export interface UseDashboardUrlParams {
  engagement_id?: string;
  run_id?: string;
}

/**
 * Hook to get the LangSmith dashboard URL.
 *
 * @param params - Optional parameters to filter the dashboard view
 * @returns Query result with dashboard URL
 *
 * @example
 * const { data } = useDashboardUrl({ engagement_id: 'eng-123' });
 * // Navigate to data.url
 */
export function useDashboardUrl(params?: UseDashboardUrlParams) {
  return useQuery<DashboardUrlResponse>({
    queryKey: observabilityKeys.dashboardUrl(params ?? {}),
    queryFn: () => getDashboardUrl(params),
    staleTime: 5 * 60 * 1000, // 5 minutes - URLs don't change often
  });
}

// ============================================================================
// Health Check Hook
// ============================================================================

/**
 * Hook to check LangSmith integration health.
 *
 * @returns Query result with health status
 *
 * @example
 * const { data: health } = useLangSmithHealth();
 * if (health?.connected) {
 *   // LangSmith is available
 * }
 */
export function useLangSmithHealth() {
  return useQuery<LangSmithHealth>({
    queryKey: observabilityKeys.health(),
    queryFn: () => getLangSmithHealth(),
    staleTime: 60 * 1000, // 1 minute
    retry: 1, // Don't retry too much for health checks
  });
}

// ============================================================================
// Convenience Hooks
// ============================================================================

/**
 * Hook that combines traces and stats for an engagement.
 * Useful for observability dashboard views.
 *
 * @param engagementId - The engagement ID
 * @returns Combined traces and stats data
 */
export function useEngagementObservability(engagementId: string | undefined) {
  const traces = useEngagementTraces(engagementId);
  const stats = useObservabilityStats(
    engagementId ? { engagement_id: engagementId } : undefined
  );
  const dashboardUrl = useDashboardUrl(
    engagementId ? { engagement_id: engagementId } : undefined
  );

  return {
    traces: traces.data,
    stats: stats.data,
    dashboardUrl: dashboardUrl.data?.url,
    isLoading: traces.isLoading || stats.isLoading,
    isError: traces.isError || stats.isError,
    error: traces.error || stats.error,
    refetch: () => {
      traces.refetch();
      stats.refetch();
    },
  };
}

/**
 * Hook to check if LangSmith is available and properly configured.
 *
 * @returns Boolean indicating if LangSmith is available
 */
export function useLangSmithAvailable() {
  const health = useLangSmithHealth();
  return {
    isAvailable: health.data?.connected ?? false,
    isConfigured: health.data?.configured ?? false,
    isEnabled: health.data?.enabled ?? false,
    isLoading: health.isLoading,
    project: health.data?.project,
    endpoint: health.data?.endpoint,
  };
}
