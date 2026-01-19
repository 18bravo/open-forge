'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getReviews,
  getReview,
  getReviewStats,
  completeReview,
  deferReview,
  skipReview,
  ReviewStatus,
  ReviewCategory,
} from '../api';

export function useReviews(params?: {
  page?: number;
  page_size?: number;
  status?: ReviewStatus;
  category?: ReviewCategory;
}) {
  return useQuery({
    queryKey: ['reviews', params],
    queryFn: () => getReviews(params),
  });
}

export function useReview(id: string) {
  return useQuery({
    queryKey: ['reviews', id],
    queryFn: () => getReview(id),
    enabled: !!id,
  });
}

export function useReviewStats() {
  return useQuery({
    queryKey: ['reviews', 'stats'],
    queryFn: getReviewStats,
    refetchInterval: 30000,
  });
}

export function useCompleteReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, result }: { id: string; result: Record<string, unknown> }) =>
      completeReview(id, result),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });
}

export function useDeferReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => deferReview(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });
}

export function useSkipReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => skipReview(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });
}
