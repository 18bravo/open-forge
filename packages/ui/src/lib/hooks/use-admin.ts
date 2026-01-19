'use client';

import { useQuery } from '@tanstack/react-query';
import { getSystemHealth, getDashboardStats, getRecentAlerts } from '../api';

export function useSystemHealth() {
  return useQuery({
    queryKey: ['admin', 'health'],
    queryFn: getSystemHealth,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['admin', 'dashboard', 'stats'],
    queryFn: getDashboardStats,
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useRecentAlerts(limit: number = 10) {
  return useQuery({
    queryKey: ['admin', 'alerts', limit],
    queryFn: () => getRecentAlerts(limit),
    refetchInterval: 30000,
  });
}
