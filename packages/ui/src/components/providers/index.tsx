'use client';

import * as React from 'react';

import { ThemeProvider } from './theme-provider';
import { QueryProvider } from './query-provider';
import { AuthProvider } from './auth-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToastProvider, ToastViewport } from '@/components/ui/toast';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryProvider>
      <ThemeProvider>
        <AuthProvider>
          <TooltipProvider>
            <ToastProvider>
              {children}
              <ToastViewport />
            </ToastProvider>
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryProvider>
  );
}

// Re-export individual providers for granular usage
export { ThemeProvider } from './theme-provider';
export { QueryProvider } from './query-provider';
export { AuthProvider, useAuth } from './auth-provider';
