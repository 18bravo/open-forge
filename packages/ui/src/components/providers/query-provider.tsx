'use client';

import * as React from 'react';
import {
  QueryClient,
  QueryClientProvider,
  QueryClientConfig,
} from '@tanstack/react-query';

interface QueryProviderProps {
  children: React.ReactNode;
}

const queryClientConfig: QueryClientConfig = {
  defaultOptions: {
    queries: {
      // Stale time of 1 minute
      staleTime: 60 * 1000,
      // Cache time of 5 minutes
      gcTime: 5 * 60 * 1000,
      // Retry failed requests up to 3 times
      retry: 3,
      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Refetch on window focus
      refetchOnWindowFocus: false,
    },
    mutations: {
      // Retry mutations once
      retry: 1,
    },
  },
};

function makeQueryClient() {
  return new QueryClient(queryClientConfig);
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    // This is very important so we don't re-make a new client if React
    // suspends during the initial render. This may not be needed if we
    // have a suspense boundary BELOW the creation of the query client
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

export function QueryProvider({ children }: QueryProviderProps) {
  // NOTE: Avoid useState when initializing the query client if you don't
  //       have a suspense boundary between this and the code that may
  //       suspend because React will throw away the client on the initial
  //       render if it suspends and there is no boundary
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
