'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAgentClusters, getAgentCluster, getAgentTypes, scaleAgentCluster } from '../api';

export function useAgentClusters() {
  return useQuery({
    queryKey: ['admin', 'agents', 'clusters'],
    queryFn: getAgentClusters,
  });
}

export function useAgentCluster(slug: string) {
  return useQuery({
    queryKey: ['admin', 'agents', 'clusters', slug],
    queryFn: () => getAgentCluster(slug),
    enabled: !!slug,
  });
}

export function useAgentTypes() {
  return useQuery({
    queryKey: ['admin', 'agents', 'types'],
    queryFn: getAgentTypes,
  });
}

export function useScaleCluster() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, targetInstances }: { slug: string; targetInstances: number }) =>
      scaleAgentCluster(slug, targetInstances),
    onSuccess: (_, { slug }) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'agents', 'clusters'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'agents', 'clusters', slug] });
    },
  });
}
