/**
 * StateManager
 *
 * Centralized state management for studio applications using Zustand.
 * Handles global state, page state, and widget state with Immer integration.
 */

import React from 'react';
import type {
  RuntimeState,
  WidgetRuntimeState,
  StudioApp,
} from '../types';

// ============================================================================
// Types
// ============================================================================

/**
 * State manager store interface
 */
export interface StudioStateStore {
  /** Current runtime state */
  state: RuntimeState;

  /** Initialize state from app definition */
  initialize: (app: StudioApp, initialPageId?: string, initialParams?: Record<string, unknown>) => void;

  /** Reset state to initial values */
  reset: () => void;

  // Navigation
  /** Navigate to a page */
  navigateTo: (pageId: string, params?: Record<string, unknown>) => void;

  /** Update page parameters */
  setPageParams: (params: Record<string, unknown>) => void;

  // Global State
  /** Set a global state value */
  setGlobalState: (key: string, value: unknown) => void;

  /** Get a global state value */
  getGlobalState: <T = unknown>(key: string) => T | undefined;

  /** Merge global state values */
  mergeGlobalState: (values: Record<string, unknown>) => void;

  // Page State
  /** Set a page state value */
  setPageState: (key: string, value: unknown) => void;

  /** Get a page state value */
  getPageState: <T = unknown>(key: string) => T | undefined;

  /** Merge page state values */
  mergePageState: (values: Record<string, unknown>) => void;

  /** Clear page state */
  clearPageState: () => void;

  // Widget State
  /** Set widget state */
  setWidgetState: (widgetId: string, state: Partial<WidgetRuntimeState>) => void;

  /** Get widget state */
  getWidgetState: (widgetId: string) => WidgetRuntimeState | undefined;

  /** Clear widget state */
  clearWidgetState: (widgetId: string) => void;

  // Loading/Error States
  /** Set loading state for a binding */
  setLoading: (bindingId: string, isLoading: boolean) => void;

  /** Set error state for a binding */
  setError: (bindingId: string, error: Error | null) => void;

  // Data Cache
  /** Set cached data for a binding */
  setCachedData: (bindingId: string, data: unknown) => void;

  /** Get cached data for a binding */
  getCachedData: <T = unknown>(bindingId: string) => T | undefined;

  /** Clear cached data */
  clearCache: (bindingIds?: string[]) => void;

  // Subscriptions
  /** Subscribe to state changes */
  subscribe: (selector: (state: RuntimeState) => unknown, callback: () => void) => () => void;
}

/**
 * Initial runtime state
 */
export const initialRuntimeState: RuntimeState = {
  currentPageId: '',
  pageParams: {},
  globalState: {},
  pageState: {},
  widgetStates: {},
  loadingStates: {},
  errorStates: {},
  dataCache: {},
};

// ============================================================================
// Store Creation
// ============================================================================

/**
 * Create a studio state store
 * Uses Zustand with Immer middleware for immutable updates
 */
export function createStudioStore(): StudioStateStore {
  // TODO: Implement with Zustand
  // TODO: Implement with Immer middleware
  // TODO: Implement persistence (optional)
  // TODO: Implement devtools integration

  return {
    state: initialRuntimeState,
    initialize: () => {},
    reset: () => {},
    navigateTo: () => {},
    setPageParams: () => {},
    setGlobalState: () => {},
    getGlobalState: () => undefined,
    mergeGlobalState: () => {},
    setPageState: () => {},
    getPageState: () => undefined,
    mergePageState: () => {},
    clearPageState: () => {},
    setWidgetState: () => {},
    getWidgetState: () => undefined,
    clearWidgetState: () => {},
    setLoading: () => {},
    setError: () => {},
    setCachedData: () => {},
    getCachedData: () => undefined,
    clearCache: () => {},
    subscribe: () => () => {},
  };
}

// ============================================================================
// Context
// ============================================================================

export const StateManagerContext = React.createContext<StudioStateStore | null>(null);

/**
 * Hook to access state manager
 */
export function useStateManager(): StudioStateStore {
  const context = React.useContext(StateManagerContext);
  if (!context) {
    throw new Error('useStateManager must be used within a StateManagerProvider');
  }
  return context;
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook to access runtime state
 */
export function useRuntimeState(): RuntimeState {
  const store = useStateManager();
  return store.state;
}

/**
 * Hook to access current page
 */
export function useCurrentPage(): { pageId: string; params: Record<string, unknown> } {
  const store = useStateManager();
  return {
    pageId: store.state.currentPageId,
    params: store.state.pageParams,
  };
}

/**
 * Hook to access global state
 */
export function useGlobalState<T = unknown>(key: string): [T | undefined, (value: T) => void] {
  const store = useStateManager();

  return [
    store.getGlobalState<T>(key),
    (value: T) => store.setGlobalState(key, value),
  ];
}

/**
 * Hook to access page state
 */
export function usePageState<T = unknown>(key: string): [T | undefined, (value: T) => void] {
  const store = useStateManager();

  return [
    store.getPageState<T>(key),
    (value: T) => store.setPageState(key, value),
  ];
}

/**
 * Hook to access widget state
 */
export function useWidgetState(
  widgetId: string
): [WidgetRuntimeState | undefined, (state: Partial<WidgetRuntimeState>) => void] {
  const store = useStateManager();

  return [
    store.getWidgetState(widgetId),
    (state: Partial<WidgetRuntimeState>) => store.setWidgetState(widgetId, state),
  ];
}

/**
 * Hook for navigation
 */
export function useNavigation(): {
  currentPageId: string;
  params: Record<string, unknown>;
  navigateTo: (pageId: string, params?: Record<string, unknown>) => void;
  setParams: (params: Record<string, unknown>) => void;
} {
  const store = useStateManager();

  return {
    currentPageId: store.state.currentPageId,
    params: store.state.pageParams,
    navigateTo: store.navigateTo,
    setParams: store.setPageParams,
  };
}

// ============================================================================
// Provider Component
// ============================================================================

export interface StateManagerProviderProps {
  /** Application definition */
  app: StudioApp;

  /** Initial page ID */
  initialPageId?: string;

  /** Initial page parameters */
  initialParams?: Record<string, unknown>;

  /** Children */
  children: React.ReactNode;
}

/**
 * Provider component for state management
 */
export const StateManagerProvider: React.FC<StateManagerProviderProps> = ({
  app: _app,
  initialPageId: _initialPageId,
  initialParams: _initialParams,
  children,
}) => {
  // TODO: Create store instance
  // TODO: Initialize with app state
  // TODO: Handle navigation

  const store = createStudioStore();

  return (
    <StateManagerContext.Provider value={store}>
      {children}
    </StateManagerContext.Provider>
  );
};

StateManagerProvider.displayName = 'StateManagerProvider';

export default StateManagerProvider;
