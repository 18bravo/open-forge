'use client';

import { useQuery } from '@tanstack/react-query';
import { getDashboardMetrics, type DashboardMetrics } from '../api';

export function useDashboardMetrics() {
  return useQuery<DashboardMetrics>({
    queryKey: ['dashboard', 'metrics'],
    queryFn: getDashboardMetrics,
    refetchInterval: 60000, // Refresh every minute
  });
}
