'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getPipelines,
  getPipeline,
  getPipelineRuns,
  triggerPipelineRun,
  updatePipelineStatus,
  PipelineRunStatus,
  PipelineStatus,
} from '../api';

export function usePipelines(params?: { page?: number; page_size?: number; active_only?: boolean }) {
  return useQuery({
    queryKey: ['admin', 'pipelines', params],
    queryFn: () => getPipelines(params),
  });
}

export function usePipeline(id: string) {
  return useQuery({
    queryKey: ['admin', 'pipelines', id],
    queryFn: () => getPipeline(id),
    enabled: !!id,
  });
}

export function usePipelineRuns(params?: { page?: number; page_size?: number; pipeline_id?: string; status?: PipelineRunStatus }) {
  return useQuery({
    queryKey: ['admin', 'pipelines', 'runs', params],
    queryFn: () => getPipelineRuns(params),
  });
}

export function useTriggerPipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pipelineId: string) => triggerPipelineRun(pipelineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'pipelines'] });
    },
  });
}

export function useUpdatePipelineStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ pipelineId, status }: { pipelineId: string; status: PipelineStatus }) =>
      updatePipelineStatus(pipelineId, status),
    onSuccess: (_, { pipelineId }) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'pipelines'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'pipelines', pipelineId] });
    },
  });
}
