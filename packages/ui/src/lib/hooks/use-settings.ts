'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getSystemSettings,
  updateSystemSettings,
  getConnectors,
  testConnector,
  getUsers,
  getAuditLogs,
  SystemSettings,
} from '../api';

export function useSystemSettings() {
  return useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: getSystemSettings,
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: Partial<SystemSettings>) => updateSystemSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'settings'] });
    },
  });
}

export function useConnectors(params?: { page?: number; page_size?: number; type?: string }) {
  return useQuery({
    queryKey: ['admin', 'connectors', params],
    queryFn: () => getConnectors(params),
  });
}

export function useTestConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (connectorId: string) => testConnector(connectorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'connectors'] });
    },
  });
}

export function useUsers(params?: { page?: number; page_size?: number; role?: string; status?: string }) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => getUsers(params),
  });
}

export function useAuditLogs(params?: { page?: number; page_size?: number; category?: string; actor?: string }) {
  return useQuery({
    queryKey: ['admin', 'audit', params],
    queryFn: () => getAuditLogs(params),
  });
}
