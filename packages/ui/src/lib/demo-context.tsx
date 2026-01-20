'use client';

import { createContext, useContext, type ReactNode } from 'react';

/**
 * Demo mode context
 * When true, API calls return mock data instead of hitting the real backend
 */
const DemoContext = createContext<boolean>(false);

/**
 * Hook to check if we're in demo mode
 */
export function useIsDemo(): boolean {
  return useContext(DemoContext);
}

/**
 * Provider component that enables demo mode for its children
 */
export function DemoModeProvider({ children }: { children: ReactNode }) {
  return (
    <DemoContext.Provider value={true}>
      {children}
    </DemoContext.Provider>
  );
}

/**
 * Global flag for demo mode detection in non-React contexts (like API calls)
 * This is set by the demo layout and checked by apiFetch
 */
let globalDemoMode = false;

export function setGlobalDemoMode(enabled: boolean) {
  globalDemoMode = enabled;
}

export function isGlobalDemoMode(): boolean {
  return globalDemoMode;
}
