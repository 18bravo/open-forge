'use client';

import { useQuery } from '@tanstack/react-query';
import { getEngagementActivities, getRecentActivities, type ActivityItem } from '../api';

export function useEngagementActivities(engagementId: string | undefined, limit: number = 20) {
  return useQuery<{ items: ActivityItem[] }>({
    queryKey: ['activities', 'engagement', engagementId, limit],
    queryFn: () => getEngagementActivities(engagementId!, limit),
    enabled: !!engagementId,
  });
}

export function useRecentActivities(limit: number = 10) {
  return useQuery<{ items: ActivityItem[] }>({
    queryKey: ['activities', 'recent', limit],
    queryFn: () => getRecentActivities(limit),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}
