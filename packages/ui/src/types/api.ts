/**
 * API Response Types
 *
 * These types match the backend FastAPI schemas and are used
 * for type-safe API interactions.
 */

// Generic paginated response wrapper
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Generic API error response
export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

// Health check response
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    database: 'up' | 'down';
    cache?: 'up' | 'down';
    queue?: 'up' | 'down';
  };
}

// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: UserResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
  created_at: string;
  updated_at: string;
}

// Request/Response types for mutations
export interface CreateResourceResponse<T> {
  data: T;
  message: string;
}

export interface UpdateResourceResponse<T> {
  data: T;
  message: string;
}

export interface DeleteResourceResponse {
  message: string;
  deleted_at: string;
}

// Query parameters for list endpoints
export interface ListQueryParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  search?: string;
}

// Export re-exports from api.ts for convenience
export type {
  EngagementStatus,
  EngagementPriority,
  DataSourceType,
  DataSourceStatus,
  ApprovalType,
  ApprovalStatus,
  AgentTaskStatus,
} from '@/lib/api';
