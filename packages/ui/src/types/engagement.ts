/**
 * Engagement Types
 *
 * Types for engagement management features.
 */

import type {
  EngagementStatus,
  EngagementPriority,
  DataSourceReference,
} from '@/lib/api';

// Engagement entity
export interface Engagement {
  id: string;
  name: string;
  description?: string;
  objective: string;
  status: EngagementStatus;
  priority: EngagementPriority;
  data_sources: DataSourceReference[];
  agent_config?: EngagementAgentConfig;
  tags: string[];
  metadata?: Record<string, unknown>;
  requires_approval: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

// Engagement summary for list views
export interface EngagementSummary {
  id: string;
  name: string;
  status: EngagementStatus;
  priority: EngagementPriority;
  created_by: string;
  created_at: string;
  updated_at: string;
  task_count?: number;
  completion_percentage?: number;
}

// Agent configuration for engagement
export interface EngagementAgentConfig {
  model?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: string[];
  system_prompt?: string;
  max_iterations?: number;
  timeout_seconds?: number;
}

// Form data for creating/editing engagements
export interface EngagementFormData {
  name: string;
  description?: string;
  objective: string;
  priority: EngagementPriority;
  data_sources: DataSourceReference[];
  agent_config?: EngagementAgentConfig;
  tags: string[];
  metadata?: Record<string, unknown>;
  requires_approval: boolean;
}

// Status transition rules
export const ENGAGEMENT_STATUS_TRANSITIONS: Record<EngagementStatus, EngagementStatus[]> = {
  draft: ['pending_approval', 'cancelled'],
  pending_approval: ['approved', 'cancelled'],
  approved: ['in_progress', 'cancelled'],
  in_progress: ['paused', 'completed', 'failed', 'cancelled'],
  paused: ['in_progress', 'cancelled'],
  completed: [],
  cancelled: [],
  failed: ['draft'],
};

// Status display configuration
export const ENGAGEMENT_STATUS_CONFIG: Record<
  EngagementStatus,
  { label: string; color: string; bgColor: string }
> = {
  draft: { label: 'Draft', color: 'text-gray-600', bgColor: 'bg-gray-100' },
  pending_approval: { label: 'Pending Approval', color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  approved: { label: 'Approved', color: 'text-blue-600', bgColor: 'bg-blue-100' },
  in_progress: { label: 'In Progress', color: 'text-indigo-600', bgColor: 'bg-indigo-100' },
  paused: { label: 'Paused', color: 'text-orange-600', bgColor: 'bg-orange-100' },
  completed: { label: 'Completed', color: 'text-green-600', bgColor: 'bg-green-100' },
  cancelled: { label: 'Cancelled', color: 'text-gray-500', bgColor: 'bg-gray-100' },
  failed: { label: 'Failed', color: 'text-red-600', bgColor: 'bg-red-100' },
};

// Priority display configuration
export const ENGAGEMENT_PRIORITY_CONFIG: Record<
  EngagementPriority,
  { label: string; color: string; bgColor: string }
> = {
  low: { label: 'Low', color: 'text-gray-600', bgColor: 'bg-gray-100' },
  medium: { label: 'Medium', color: 'text-blue-600', bgColor: 'bg-blue-100' },
  high: { label: 'High', color: 'text-orange-600', bgColor: 'bg-orange-100' },
  critical: { label: 'Critical', color: 'text-red-600', bgColor: 'bg-red-100' },
};

// Helper type for engagement filters
export interface EngagementFilters {
  status?: EngagementStatus[];
  priority?: EngagementPriority[];
  tags?: string[];
  created_by?: string;
  date_range?: {
    start: string;
    end: string;
  };
}
