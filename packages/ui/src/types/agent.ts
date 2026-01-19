/**
 * Agent Types
 *
 * Types for AI agent features including tasks, messages, and tool execution.
 */

import type { AgentTaskStatus } from '@/lib/api';

// Tool call representation
export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  error?: string;
  executed_at?: string;
  duration_ms?: number;
  requires_approval?: boolean;
}

// Agent message in conversation
export interface AgentMessage {
  id: string;
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: ToolCall[];
  timestamp: string;
  metadata?: {
    model?: string;
    tokens_used?: number;
    latency_ms?: number;
  };
}

// Agent task entity
export interface AgentTask {
  id: string;
  engagement_id: string;
  task_type: AgentTaskType;
  description: string;
  status: AgentTaskStatus;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  tools: string[];
  max_iterations: number;
  current_iteration: number;
  timeout_seconds: number;
  messages: AgentMessage[];
  pending_tool_approvals: ToolCall[];
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  metadata?: Record<string, unknown>;
}

// Agent task summary for list views
export interface AgentTaskSummary {
  id: string;
  engagement_id: string;
  task_type: AgentTaskType;
  description: string;
  status: AgentTaskStatus;
  current_iteration: number;
  max_iterations: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  has_pending_approvals: boolean;
}

// Predefined task types
export type AgentTaskType =
  | 'data_analysis'
  | 'data_transformation'
  | 'report_generation'
  | 'schema_discovery'
  | 'data_validation'
  | 'custom';

// Form data for creating agent tasks
export interface AgentTaskFormData {
  engagement_id: string;
  task_type: AgentTaskType;
  description: string;
  input_data?: Record<string, unknown>;
  tools?: string[];
  max_iterations?: number;
  timeout_seconds?: number;
}

// Tool approval decision
export interface ToolApprovalDecision {
  tool_call_id: string;
  approved: boolean;
  reason?: string;
}

// Available tools configuration
export interface AvailableTool {
  name: string;
  description: string;
  category: ToolCategory;
  requires_approval: boolean;
  parameters: ToolParameter[];
}

export type ToolCategory =
  | 'data_access'
  | 'data_transformation'
  | 'file_operations'
  | 'external_api'
  | 'system';

export interface ToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  default?: unknown;
}

// Status display configuration
export const AGENT_TASK_STATUS_CONFIG: Record<
  AgentTaskStatus,
  { label: string; color: string; bgColor: string }
> = {
  pending: { label: 'Pending', color: 'text-gray-600', bgColor: 'bg-gray-100' },
  queued: { label: 'Queued', color: 'text-blue-600', bgColor: 'bg-blue-100' },
  running: { label: 'Running', color: 'text-indigo-600', bgColor: 'bg-indigo-100' },
  waiting_approval: { label: 'Waiting Approval', color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  completed: { label: 'Completed', color: 'text-green-600', bgColor: 'bg-green-100' },
  failed: { label: 'Failed', color: 'text-red-600', bgColor: 'bg-red-100' },
  cancelled: { label: 'Cancelled', color: 'text-gray-500', bgColor: 'bg-gray-100' },
};

// Task type display configuration
export const AGENT_TASK_TYPE_CONFIG: Record<
  AgentTaskType,
  { label: string; description: string }
> = {
  data_analysis: {
    label: 'Data Analysis',
    description: 'Analyze data patterns and generate insights',
  },
  data_transformation: {
    label: 'Data Transformation',
    description: 'Transform and reshape data structures',
  },
  report_generation: {
    label: 'Report Generation',
    description: 'Generate reports and documentation',
  },
  schema_discovery: {
    label: 'Schema Discovery',
    description: 'Discover and document data schemas',
  },
  data_validation: {
    label: 'Data Validation',
    description: 'Validate data quality and integrity',
  },
  custom: {
    label: 'Custom Task',
    description: 'Custom agent task with specific instructions',
  },
};

// Helper type for task filters
export interface AgentTaskFilters {
  status?: AgentTaskStatus[];
  task_type?: AgentTaskType[];
  engagement_id?: string;
  has_pending_approvals?: boolean;
  date_range?: {
    start: string;
    end: string;
  };
}
