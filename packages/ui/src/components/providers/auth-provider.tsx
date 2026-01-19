'use client';

import * as React from 'react';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const isAuthenticated = !!user;

  React.useEffect(() => {
    // Check for existing session on mount
    const checkSession = async () => {
      try {
        // TODO: Implement actual session check against backend
        const storedUser = localStorage.getItem('open-forge-user');
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      } catch (error) {
        console.error('Failed to check session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkSession();
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // TODO: Implement actual login against backend API
      // const response = await apiClient.post('/auth/login', { email, password });
      // const userData = response.data.user;

      // Placeholder implementation
      const userData: User = {
        id: '1',
        email,
        name: email.split('@')[0] ?? 'User',
        role: 'user',
      };

      setUser(userData);
      localStorage.setItem('open-forge-user', JSON.stringify(userData));
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = React.useCallback(async () => {
    setIsLoading(true);
    try {
      // TODO: Implement actual logout against backend API
      // await apiClient.post('/auth/logout');

      setUser(null);
      localStorage.removeItem('open-forge-user');
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshToken = React.useCallback(async () => {
    try {
      // TODO: Implement token refresh against backend API
      // const response = await apiClient.post('/auth/refresh');
      // Update stored tokens
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, log out the user
      await logout();
      throw error;
    }
  }, [logout]);

  const value = React.useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated,
      login,
      logout,
      refreshToken,
    }),
    [user, isLoading, isAuthenticated, login, logout, refreshToken]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
