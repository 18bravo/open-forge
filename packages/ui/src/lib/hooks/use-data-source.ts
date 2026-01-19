'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDataSources,
  getDataSource,
  createDataSource,
  testDataSourceConnection,
  type DataSource,
  type DataSourceSummary,
  type DataSourceCreate,
  type DataSourceType,
  type DataSourceStatus,
  type PaginatedResponse,
} from '@/lib/api';

// Query keys
export const dataSourceKeys = {
  all: ['dataSources'] as const,
  lists: () => [...dataSourceKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...dataSourceKeys.lists(), filters] as const,
  details: () => [...dataSourceKeys.all, 'detail'] as const,
  detail: (id: string) => [...dataSourceKeys.details(), id] as const,
};

// Fetch data sources list
export function useDataSources(params?: {
  page?: number;
  page_size?: number;
  type?: DataSourceType;
  status?: DataSourceStatus;
  search?: string;
}) {
  return useQuery<PaginatedResponse<DataSourceSummary>>({
    queryKey: dataSourceKeys.list(params ?? {}),
    queryFn: () => getDataSources(params),
  });
}

// Fetch single data source
export function useDataSource(id: string | undefined) {
  return useQuery<DataSource>({
    queryKey: dataSourceKeys.detail(id ?? ''),
    queryFn: () => getDataSource(id!),
    enabled: !!id,
  });
}

// Create data source mutation
export function useCreateDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DataSourceCreate) => createDataSource(data),
    onSuccess: () => {
      // Invalidate and refetch data sources list
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() });
    },
  });
}

// Test data source connection mutation
export function useTestDataSourceConnection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => testDataSourceConnection(id),
    onSuccess: (_, id) => {
      // Invalidate to refetch updated test status
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() });
    },
  });
}
