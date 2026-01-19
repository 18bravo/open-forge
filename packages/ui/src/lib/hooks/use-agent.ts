'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAgentTasks,
  getAllAgentTasks,
  getAgentTask,
  approveToolCall,
  type AgentTask,
  type AgentTaskSummary,
  type AgentTaskStatus,
  type PaginatedResponse,
} from '@/lib/api';

// Query keys
export const agentKeys = {
  all: ['agents'] as const,
  tasks: () => [...agentKeys.all, 'tasks'] as const,
  allTasks: (filters: Record<string, unknown>) =>
    [...agentKeys.tasks(), 'all', filters] as const,
  taskList: (engagementId: string, filters: Record<string, unknown>) =>
    [...agentKeys.tasks(), engagementId, filters] as const,
  taskDetails: () => [...agentKeys.tasks(), 'detail'] as const,
  taskDetail: (id: string) => [...agentKeys.taskDetails(), id] as const,
};

// Fetch all agent tasks (not filtered by engagement)
export function useAllAgentTasks(params?: {
  page?: number;
  page_size?: number;
  status?: AgentTaskStatus;
  cluster?: string;
}) {
  return useQuery<PaginatedResponse<AgentTaskSummary>>({
    queryKey: agentKeys.allTasks(params ?? {}),
    queryFn: () => getAllAgentTasks(params),
  });
}

// Fetch agent tasks for an engagement
export function useAgentTasks(
  engagementId: string | undefined,
  params?: {
    page?: number;
    page_size?: number;
    status?: AgentTaskStatus;
  }
) {
  return useQuery<PaginatedResponse<AgentTaskSummary>>({
    queryKey: agentKeys.taskList(engagementId ?? '', params ?? {}),
    queryFn: () => getAgentTasks(engagementId!, params),
    enabled: !!engagementId,
  });
}

// Fetch single agent task
export function useAgentTask(taskId: string | undefined) {
  return useQuery<AgentTask>({
    queryKey: agentKeys.taskDetail(taskId ?? ''),
    queryFn: () => getAgentTask(taskId!),
    enabled: !!taskId,
    // Poll for updates when task is running or waiting for approval
    refetchInterval: (query) => {
      const data = query.state.data as AgentTask | undefined;
      if (
        data?.status === 'running' ||
        data?.status === 'waiting_approval' ||
        data?.status === 'queued'
      ) {
        return 3000; // Poll every 3 seconds
      }
      return false;
    },
  });
}

// Approve or reject tool call
export function useApproveToolCall() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskId,
      toolCallId,
      approved,
      reason,
    }: {
      taskId: string;
      toolCallId: string;
      approved: boolean;
      reason?: string;
    }) => approveToolCall(taskId, toolCallId, approved, reason),
    onSuccess: (data, variables) => {
      // Update the cache directly
      queryClient.setQueryData(agentKeys.taskDetail(variables.taskId), data);
    },
  });
}

// Hook for real-time task updates via WebSocket (placeholder)
export function useAgentTaskStream(taskId: string | undefined) {
  // TODO: Implement WebSocket connection for real-time updates
  // This would connect to a WebSocket endpoint like /ws/tasks/{taskId}
  // For now, we rely on polling in useAgentTask

  return {
    isConnected: false,
    messages: [] as AgentTask['messages'],
    error: null as Error | null,
  };
}
