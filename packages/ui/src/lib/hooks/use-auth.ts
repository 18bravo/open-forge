'use client';

import { useCallback } from 'react';
import { useAuth as useAuthContext, type User } from '@/components/providers/auth-provider';

/**
 * Hook for accessing authentication state and methods
 */
export function useAuth() {
  const context = useAuthContext();
  return context;
}

/**
 * Hook for checking if user has specific role
 */
export function useHasRole(requiredRole: User['role'] | User['role'][]) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return false;
  }

  const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];

  // Admin has access to everything
  if (user.role === 'admin') {
    return true;
  }

  return roles.includes(user.role);
}

/**
 * Hook for role-based access control
 */
export function useRBAC() {
  const { user, isAuthenticated } = useAuth();

  const can = useCallback(
    (action: string, resource?: string) => {
      if (!isAuthenticated || !user) {
        return false;
      }

      // Define permission matrix
      const permissions: Record<string, Record<string, User['role'][]>> = {
        engagement: {
          create: ['admin', 'user'],
          read: ['admin', 'user', 'viewer'],
          update: ['admin', 'user'],
          delete: ['admin'],
          approve: ['admin'],
        },
        agent: {
          create: ['admin', 'user'],
          read: ['admin', 'user', 'viewer'],
          execute: ['admin', 'user'],
          approve_tools: ['admin'],
        },
        data_source: {
          create: ['admin'],
          read: ['admin', 'user', 'viewer'],
          update: ['admin'],
          delete: ['admin'],
          test: ['admin', 'user'],
        },
        settings: {
          read: ['admin', 'user', 'viewer'],
          update: ['admin'],
        },
        team: {
          read: ['admin', 'user', 'viewer'],
          manage: ['admin'],
        },
      };

      // Admin can do everything
      if (user.role === 'admin') {
        return true;
      }

      // Check specific permission
      if (resource) {
        const resourcePermissions = permissions[resource];
        if (resourcePermissions) {
          const allowedRoles = resourcePermissions[action];
          if (allowedRoles) {
            return allowedRoles.includes(user.role);
          }
        }
      }

      return false;
    },
    [isAuthenticated, user]
  );

  return {
    can,
    user,
    isAuthenticated,
    isAdmin: user?.role === 'admin',
    isUser: user?.role === 'user',
    isViewer: user?.role === 'viewer',
  };
}

/**
 * Hook for protected route check
 */
export function useRequireAuth(redirectTo: string = '/login') {
  const { isAuthenticated, isLoading } = useAuth();

  return {
    isAuthenticated,
    isLoading,
    shouldRedirect: !isLoading && !isAuthenticated,
    redirectTo,
  };
}

export type { User };
