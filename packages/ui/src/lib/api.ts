/**
 * API client for Open Forge backend
 */

import { isGlobalDemoMode } from './demo-context';
import {
  demoEngagements,
  demoEngagementDetails,
  demoDataSources,
  demoDataSourceDetails,
  demoApprovals,
  demoApprovalDetails,
  demoActivities,
  demoDashboardMetrics,
  demoAgentClusters,
  demoAgentClusterDetails,
  demoAgentTypes,
  demoAgentTasks,
  demoAgentTaskDetails,
  demoSystemHealth,
  demoAdminDashboardStats,
  demoAlerts,
  demoPipelines,
  demoPipelineDetails,
  demoPipelineRuns,
  demoSystemSettings,
  demoConnectors,
  demoUsers,
  demoAuditLogs,
  demoReviews,
  demoReviewDetails,
  demoReviewStats,
  paginateDemo,
} from './demo-data';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Engagement status enum matching API schema
 */
export type EngagementStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'in_progress'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'failed';

/**
 * Engagement priority enum
 */
export type EngagementPriority = 'low' | 'medium' | 'high' | 'critical';

/**
 * Data source type enum
 */
export type DataSourceType =
  | 'postgresql'
  | 'mysql'
  | 's3'
  | 'gcs'
  | 'azure_blob'
  | 'iceberg'
  | 'delta'
  | 'parquet'
  | 'csv'
  | 'api'
  | 'kafka';

/**
 * Data source status enum
 */
export type DataSourceStatus = 'active' | 'inactive' | 'error' | 'testing';

/**
 * Approval type enum
 */
export type ApprovalType =
  | 'engagement'
  | 'tool_execution'
  | 'data_access'
  | 'schema_change'
  | 'deployment';

/**
 * Approval status enum
 */
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'cancelled';

/**
 * Agent task status enum
 */
export type AgentTaskStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'waiting_approval'
  | 'completed'
  | 'failed'
  | 'cancelled';

// Interfaces matching API schemas

export interface DataSourceReference {
  source_id: string;
  source_type: string;
  access_mode: string;
  config?: Record<string, unknown>;
}

export interface Engagement {
  id: string;
  name: string;
  description?: string;
  objective: string;
  status: EngagementStatus;
  priority: EngagementPriority;
  data_sources: DataSourceReference[];
  agent_config?: Record<string, unknown>;
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

export interface EngagementSummary {
  id: string;
  name: string;
  status: EngagementStatus;
  priority: EngagementPriority;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface EngagementCreate {
  name: string;
  description?: string;
  objective: string;
  priority?: EngagementPriority;
  data_sources?: DataSourceReference[];
  agent_config?: Record<string, unknown>;
  tags?: string[];
  metadata?: Record<string, unknown>;
  requires_approval?: boolean;
}

export interface DataSource {
  id: string;
  name: string;
  description?: string;
  source_type: DataSourceType;
  status: DataSourceStatus;
  connection_config: Record<string, unknown>;
  schema_config?: Record<string, unknown>;
  tags: string[];
  metadata?: Record<string, unknown>;
  created_by: string;
  created_at: string;
  updated_at: string;
  last_tested_at?: string;
  last_error?: string;
}

export interface DataSourceSummary {
  id: string;
  name: string;
  source_type: DataSourceType;
  status: DataSourceStatus;
  created_at: string;
}

export interface DataSourceCreate {
  name: string;
  description?: string;
  source_type: DataSourceType;
  connection_config: Record<string, unknown>;
  schema_config?: Record<string, unknown>;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ApprovalRequest {
  id: string;
  approval_type: ApprovalType;
  status: ApprovalStatus;
  title: string;
  description: string;
  resource_id: string;
  resource_type: string;
  requested_by: string;
  requested_at: string;
  details: Record<string, unknown>;
  expires_at?: string;
  approved_by?: string;
  approved_at?: string;
  rejection_reason?: string;
  // Extended fields for UI compatibility
  engagement_id?: string;
  escalation_level?: string;
  deadline?: string;
  context_data?: Record<string, unknown>;
  decided_by?: string;
  decided_at?: string;
  decision_comments?: string;
}

export interface ApprovalRequestSummary {
  id: string;
  approval_type: ApprovalType;
  status: ApprovalStatus;
  title: string;
  resource_id: string;
  requested_by: string;
  requested_at: string;
  expires_at?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  error?: string;
  executed_at?: string;
  duration_ms?: number;
  status?: 'pending' | 'running' | 'completed' | 'failed';
}

export interface AgentMessage {
  id: string;
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: ToolCall[];
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface AgentTask {
  id: string;
  engagement_id: string;
  task_type: string;
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

export interface AgentTaskSummary {
  id: string;
  engagement_id: string;
  task_type: string;
  status: AgentTaskStatus;
  current_iteration: number;
  created_at: string;
  completed_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// API functions

/**
 * Returns mock data for demo mode based on endpoint
 */
function getDemoResponse<T>(endpoint: string): T {
  // Parse endpoint and query params
  const [path, queryString] = endpoint.split('?');
  const params = new URLSearchParams(queryString || '');
  const page = parseInt(params.get('page') || '1');
  const pageSize = parseInt(params.get('page_size') || '10');

  // Engagements
  if (path === '/engagements') {
    return paginateDemo(demoEngagements, page, pageSize) as T;
  }
  if (path.match(/^\/engagements\/[\w-]+$/)) {
    const id = path.split('/')[2];
    return (demoEngagementDetails[id] || demoEngagementDetails['eng-001']) as T;
  }

  // Data Sources
  if (path === '/data-sources') {
    return paginateDemo(demoDataSources, page, pageSize) as T;
  }
  if (path.match(/^\/data-sources\/[\w-]+$/)) {
    const id = path.split('/')[2];
    return (demoDataSourceDetails[id] || demoDataSourceDetails['ds-001']) as T;
  }

  // Approvals
  if (path === '/approvals') {
    return paginateDemo(demoApprovals, page, pageSize) as T;
  }
  if (path.match(/^\/approvals\/[\w-]+$/)) {
    const id = path.split('/')[2];
    return (demoApprovalDetails[id] || demoApprovalDetails['apr-001']) as T;
  }

  // Dashboard
  if (path === '/dashboard/metrics') {
    return demoDashboardMetrics as T;
  }

  // Activities
  if (path === '/activities/recent') {
    return { items: demoActivities } as T;
  }
  if (path.match(/^\/engagements\/[\w-]+\/activities$/)) {
    return { items: demoActivities.slice(0, 5) } as T;
  }

  // Agent clusters
  if (path === '/admin/agents/clusters') {
    return paginateDemo(demoAgentClusters, page, pageSize) as T;
  }
  // Individual agent cluster
  if (path.match(/^\/admin\/agents\/clusters\/[\w-]+$/)) {
    const slug = path.split('/')[4];
    return (demoAgentClusterDetails[slug] || demoAgentClusterDetails['data-integration']) as T;
  }

  // Agent types
  if (path === '/admin/agents/types') {
    return demoAgentTypes as T;
  }

  // Agent tasks - check for engagement filter
  if (path === '/agents/tasks') {
    const engagementId = params.get('engagement_id');
    if (engagementId) {
      const engagementTasks = demoAgentTasks.filter(t => t.engagement_id === engagementId);
      return paginateDemo(engagementTasks, page, pageSize) as T;
    }
    return paginateDemo(demoAgentTasks, page, pageSize) as T;
  }
  // Individual agent task
  if (path.match(/^\/agents\/tasks\/[\w-]+$/)) {
    const id = path.split('/')[3];
    return (demoAgentTaskDetails[id] || demoAgentTaskDetails['task-001']) as T;
  }

  // Admin endpoints
  if (path === '/admin/health') {
    return demoSystemHealth as T;
  }
  if (path === '/admin/dashboard/stats') {
    return demoAdminDashboardStats as T;
  }
  if (path === '/admin/alerts') {
    return demoAlerts as T;
  }

  // Pipelines
  if (path === '/admin/pipelines') {
    return paginateDemo(demoPipelines, page, pageSize) as T;
  }
  if (path.match(/^\/admin\/pipelines\/[\w-]+$/)) {
    const id = path.split('/')[3];
    return (demoPipelineDetails[id] || demoPipelineDetails['pipeline-001']) as T;
  }
  if (path === '/admin/pipelines/runs') {
    const pipelineId = params.get('pipeline_id');
    if (pipelineId) {
      const filteredRuns = demoPipelineRuns.filter(r => r.pipeline_id === pipelineId);
      return paginateDemo(filteredRuns, page, pageSize) as T;
    }
    return paginateDemo(demoPipelineRuns, page, pageSize) as T;
  }

  // Settings
  if (path === '/admin/settings') {
    return demoSystemSettings as T;
  }
  if (path === '/admin/settings/connectors') {
    const typeFilter = params.get('type');
    if (typeFilter) {
      const filtered = demoConnectors.filter(c => c.type === typeFilter);
      return paginateDemo(filtered, page, pageSize) as T;
    }
    return paginateDemo(demoConnectors, page, pageSize) as T;
  }
  if (path === '/admin/settings/users') {
    const roleFilter = params.get('role');
    const statusFilter = params.get('status');
    let filtered = demoUsers;
    if (roleFilter) filtered = filtered.filter(u => u.role === roleFilter);
    if (statusFilter) filtered = filtered.filter(u => u.status === statusFilter);
    return paginateDemo(filtered, page, pageSize) as T;
  }
  if (path === '/admin/settings/audit') {
    const categoryFilter = params.get('category');
    if (categoryFilter) {
      const filtered = demoAuditLogs.filter(l => l.category === categoryFilter);
      return paginateDemo(filtered, page, pageSize) as T;
    }
    return paginateDemo(demoAuditLogs, page, pageSize) as T;
  }

  // Reviews
  if (path === '/reviews') {
    const statusFilter = params.get('status');
    const categoryFilter = params.get('category');
    let filtered = demoReviews;
    if (statusFilter) filtered = filtered.filter(r => r.status === statusFilter);
    if (categoryFilter) filtered = filtered.filter(r => r.category === categoryFilter);
    return paginateDemo(filtered, page, pageSize) as T;
  }
  if (path === '/reviews/stats') {
    return demoReviewStats as T;
  }
  if (path.match(/^\/reviews\/[\w-]+$/)) {
    const id = path.split('/')[2];
    return (demoReviewDetails[id] || demoReviewDetails['review-001']) as T;
  }
  // Review actions (complete, defer, skip)
  if (path.match(/^\/reviews\/[\w-]+\/(complete|defer|skip)$/)) {
    const id = path.split('/')[2];
    const detail = demoReviewDetails[id] || demoReviewDetails['review-001'];
    return { ...detail, status: 'completed' } as T;
  }

  // Approval decide action
  if (path.match(/^\/approvals\/[\w-]+\/decide$/)) {
    const id = path.split('/')[2];
    const detail = demoApprovalDetails[id] || demoApprovalDetails['apr-001'];
    return { ...detail, status: 'approved' } as T;
  }

  // Data source test connection
  if (path.match(/^\/data-sources\/[\w-]+\/test$/)) {
    return { success: true, message: 'Connection successful', latency_ms: 45 } as T;
  }

  // Agent task tool approvals
  if (path.match(/^\/agents\/tasks\/[\w-]+\/tool-approvals$/)) {
    const id = path.split('/')[3];
    return (demoAgentTaskDetails[id] || demoAgentTaskDetails['task-001']) as T;
  }

  // Connector test
  if (path.match(/^\/admin\/settings\/connectors\/[\w-]+\/test$/)) {
    return { success: true, message: 'Connection test passed', latency_ms: 32 } as T;
  }

  // Default empty response for unmatched endpoints
  return { items: [], total: 0, page: 1, page_size: pageSize, total_pages: 0 } as T;
}

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  // Check for demo mode - return mock data instead of calling real API
  if (isGlobalDemoMode()) {
    // Simulate network delay for realism
    await new Promise(resolve => setTimeout(resolve, 200 + Math.random() * 300));
    return getDemoResponse<T>(endpoint);
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API error: ${response.status}`);
  }

  return response.json();
}

// Engagements API

export async function getEngagements(params?: {
  page?: number;
  page_size?: number;
  status?: EngagementStatus;
  priority?: EngagementPriority;
  search?: string;
}): Promise<PaginatedResponse<EngagementSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.status) searchParams.set('status', params.status);
  if (params?.priority) searchParams.set('priority', params.priority);
  if (params?.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  return apiFetch(`/engagements${query ? `?${query}` : ''}`);
}

export async function getEngagement(id: string): Promise<Engagement> {
  return apiFetch(`/engagements/${id}`);
}

export async function createEngagement(data: EngagementCreate): Promise<Engagement> {
  return apiFetch('/engagements', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateEngagement(
  id: string,
  data: Partial<EngagementCreate>
): Promise<Engagement> {
  return apiFetch(`/engagements/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function updateEngagementStatus(
  id: string,
  status: EngagementStatus,
  reason?: string
): Promise<Engagement> {
  return apiFetch(`/engagements/${id}/status`, {
    method: 'POST',
    body: JSON.stringify({ status, reason }),
  });
}

// Data Sources API

export async function getDataSources(params?: {
  page?: number;
  page_size?: number;
  type?: DataSourceType;
  status?: DataSourceStatus;
  search?: string;
}): Promise<PaginatedResponse<DataSourceSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.type) searchParams.set('type', params.type);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  return apiFetch(`/data-sources${query ? `?${query}` : ''}`);
}

export async function getDataSource(id: string): Promise<DataSource> {
  return apiFetch(`/data-sources/${id}`);
}

export async function createDataSource(data: DataSourceCreate): Promise<DataSource> {
  return apiFetch('/data-sources', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function testDataSourceConnection(id: string): Promise<{
  success: boolean;
  message: string;
  details?: Record<string, unknown>;
  latency_ms?: number;
}> {
  return apiFetch(`/data-sources/${id}/test`, { method: 'POST' });
}

// Approvals API

export async function getApprovals(params?: {
  page?: number;
  page_size?: number;
  type?: ApprovalType;
  status?: ApprovalStatus;
  pending_only?: boolean;
}): Promise<PaginatedResponse<ApprovalRequestSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.type) searchParams.set('type', params.type);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.pending_only) searchParams.set('pending_only', 'true');

  const query = searchParams.toString();
  return apiFetch(`/approvals${query ? `?${query}` : ''}`);
}

export async function getApproval(id: string): Promise<ApprovalRequest> {
  return apiFetch(`/approvals/${id}`);
}

export async function decideApproval(
  id: string,
  approved: boolean,
  reason?: string
): Promise<ApprovalRequest> {
  return apiFetch(`/approvals/${id}/decide`, {
    method: 'POST',
    body: JSON.stringify({ approved, reason }),
  });
}

// Agent Tasks API

export async function getAgentTasks(
  engagementId: string,
  params?: {
    page?: number;
    page_size?: number;
    status?: AgentTaskStatus;
  }
): Promise<PaginatedResponse<AgentTaskSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.status) searchParams.set('status', params.status);

  const query = searchParams.toString();
  return apiFetch(`/agents/tasks?engagement_id=${engagementId}${query ? `&${query}` : ''}`);
}

export async function getAgentTask(taskId: string): Promise<AgentTask> {
  return apiFetch(`/agents/tasks/${taskId}`);
}

export async function approveToolCall(
  taskId: string,
  toolCallId: string,
  approved: boolean,
  reason?: string
): Promise<AgentTask> {
  return apiFetch(`/agents/tasks/${taskId}/tool-approvals`, {
    method: 'POST',
    body: JSON.stringify({
      tool_call_id: toolCallId,
      approved,
      reason,
    }),
  });
}

// ============================================================================
// Admin API Types
// ============================================================================

export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface ServiceHealth {
  service: string;
  status: ServiceStatus;
  latency: number;
  uptime: number;
  last_check: string;
}

export interface SystemHealthResponse {
  services: ServiceHealth[];
  overall_status: ServiceStatus;
  timestamp: string;
}

export interface DashboardStats {
  system_health: { healthy: number; degraded: number; unhealthy: number };
  engagements: { total: number; active: number; pending: number; completed: number };
  agents: { total_clusters: number; running_instances: number; queued_tasks: number };
  approvals: { pending: number; approved_today: number; rejected_today: number };
}

export interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  source: string;
}

// ============================================================================
// Admin API Functions
// ============================================================================

export async function getSystemHealth(): Promise<SystemHealthResponse> {
  return apiFetch('/admin/health');
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiFetch('/admin/dashboard/stats');
}

export async function getRecentAlerts(limit: number = 10): Promise<Alert[]> {
  return apiFetch(`/admin/alerts?limit=${limit}`);
}

// ============================================================================
// Pipeline Types
// ============================================================================

export type PipelineStatus = 'active' | 'paused' | 'error' | 'disabled';
export type PipelineRunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface PipelineSummary {
  id: string;
  name: string;
  description: string;
  status: PipelineStatus;
  schedule: string | null;
  last_run: string | null;
  last_run_status: PipelineRunStatus | null;
  next_run: string | null;
}

export interface PipelineDetail extends PipelineSummary {
  created_at: string;
  updated_at: string;
  config: {
    schedule: string | null;
    timeout_minutes: number;
    max_retries: number;
    concurrency: number;
  };
  stages: PipelineStage[];
}

export interface PipelineStage {
  id: string;
  name: string;
  order: number;
  type: string;
}

export interface PipelineRunSummary {
  id: string;
  pipeline_id: string;
  pipeline_name: string;
  run_number: number;
  status: PipelineRunStatus;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  triggered_by: string;
}

// ============================================================================
// Pipeline API Functions
// ============================================================================

export async function getPipelines(params?: {
  page?: number;
  page_size?: number;
  active_only?: boolean;
}): Promise<PaginatedResponse<PipelineSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.active_only) searchParams.set('active_only', 'true');
  return apiFetch(`/admin/pipelines?${searchParams}`);
}

export async function getPipeline(id: string): Promise<PipelineDetail> {
  return apiFetch(`/admin/pipelines/${id}`);
}

export async function getPipelineRuns(params?: {
  page?: number;
  page_size?: number;
  pipeline_id?: string;
  status?: PipelineRunStatus;
}): Promise<PaginatedResponse<PipelineRunSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.pipeline_id) searchParams.set('pipeline_id', params.pipeline_id);
  if (params?.status) searchParams.set('status', params.status);
  return apiFetch(`/admin/pipelines/runs?${searchParams}`);
}

export async function triggerPipelineRun(pipelineId: string): Promise<PipelineRunSummary> {
  return apiFetch(`/admin/pipelines/${pipelineId}/run`, { method: 'POST' });
}

export async function updatePipelineStatus(pipelineId: string, status: PipelineStatus): Promise<PipelineDetail> {
  return apiFetch(`/admin/pipelines/${pipelineId}/status`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  });
}

// ============================================================================
// Settings Types
// ============================================================================

export interface SystemSettings {
  instance_name: string;
  instance_url: string;
  admin_email: string;
  session_timeout_minutes: number;
  require_mfa: boolean;
  allow_self_registration: boolean;
  default_user_role: string;
}

export interface ConnectorSummary {
  id: string;
  name: string;
  type: 'database' | 'api' | 'file_storage' | 'message_queue' | 'cloud_service';
  provider: string;
  status: 'active' | 'inactive' | 'error';
  last_tested: string | null;
  last_test_success: boolean | null;
}

export interface UserSummary {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer' | 'api';
  status: 'active' | 'inactive' | 'pending';
  last_login: string | null;
  mfa_enabled: boolean;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  category: 'auth' | 'data' | 'config' | 'pipeline' | 'agent' | 'user' | 'system';
  actor: string;
  actor_type: 'user' | 'agent' | 'system';
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string | null;
}

// ============================================================================
// Settings API Functions
// ============================================================================

export async function getSystemSettings(): Promise<SystemSettings> {
  return apiFetch('/admin/settings');
}

export async function updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
  return apiFetch('/admin/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export async function getConnectors(params?: { page?: number; page_size?: number; type?: string }): Promise<PaginatedResponse<ConnectorSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.type) searchParams.set('type', params.type);
  return apiFetch(`/admin/settings/connectors?${searchParams}`);
}

export async function testConnector(connectorId: string): Promise<{ success: boolean; message: string; latency_ms: number }> {
  return apiFetch(`/admin/settings/connectors/${connectorId}/test`, { method: 'POST' });
}

export async function getUsers(params?: { page?: number; page_size?: number; role?: string; status?: string }): Promise<PaginatedResponse<UserSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.role) searchParams.set('role', params.role);
  if (params?.status) searchParams.set('status', params.status);
  return apiFetch(`/admin/settings/users?${searchParams}`);
}

export async function getAuditLogs(params?: {
  page?: number;
  page_size?: number;
  category?: string;
  actor?: string;
  start_date?: string;
  end_date?: string;
}): Promise<PaginatedResponse<AuditLogEntry>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.category) searchParams.set('category', params.category);
  if (params?.actor) searchParams.set('actor', params.actor);
  if (params?.start_date) searchParams.set('start_date', params.start_date);
  if (params?.end_date) searchParams.set('end_date', params.end_date);
  return apiFetch(`/admin/settings/audit?${searchParams}`);
}

export async function getAllAgentTasks(params?: {
  page?: number;
  page_size?: number;
  status?: AgentTaskStatus;
  cluster?: string;
}): Promise<PaginatedResponse<AgentTaskSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));
  if (params?.status) searchParams.set('status', params.status);
  if (params?.cluster) searchParams.set('cluster', params.cluster);

  const query = searchParams.toString();
  return apiFetch(`/agents/tasks${query ? `?${query}` : ''}`);
}

// ============================================================================
// Agent Cluster Types
// ============================================================================

export type ClusterStatus = 'running' | 'idle' | 'stopped' | 'error';

export interface AgentClusterSummary {
  id: string;
  name: string;
  slug: string;
  status: ClusterStatus;
  instance_count: number;
  max_instances: number;
  cpu_usage: number;
  memory_usage: number;
  queued_tasks: number;
}

export interface AgentClusterDetail extends AgentClusterSummary {
  description: string;
  agent_types: string[];
  config: {
    min_instances: number;
    max_instances: number;
    auto_scale: boolean;
    scale_up_threshold: number;
    scale_down_threshold: number;
  };
  instances: AgentInstance[];
}

export interface AgentInstance {
  id: string;
  name: string;
  status: 'running' | 'idle' | 'stopped' | 'error';
  current_task: string | null;
  started_at: string;
  cpu_usage: number;
  memory_usage: number;
}

export interface AgentTypeSummary {
  id: string;
  name: string;
  cluster: string;
  status: 'active' | 'inactive';
  task_type: string;
  version: string;
  instance_count: number;
}

// ============================================================================
// Agent Cluster API Functions
// ============================================================================

export async function getAgentClusters(): Promise<PaginatedResponse<AgentClusterSummary>> {
  return apiFetch('/admin/agents/clusters');
}

export async function getAgentCluster(slug: string): Promise<AgentClusterDetail> {
  return apiFetch(`/admin/agents/clusters/${slug}`);
}

export async function getAgentTypes(): Promise<AgentTypeSummary[]> {
  return apiFetch('/admin/agents/types');
}

export async function scaleAgentCluster(slug: string, targetInstances: number): Promise<AgentClusterDetail> {
  return apiFetch(`/admin/agents/clusters/${slug}/scale`, {
    method: 'POST',
    body: JSON.stringify({ target_instances: targetInstances }),
  });
}

// ============================================================================
// Reviews Types
// ============================================================================

export type ReviewStatus = 'queued' | 'in_review' | 'completed' | 'deferred' | 'skipped';
export type ReviewCategory = 'data_quality' | 'agent_output' | 'configuration' | 'mapping';
export type ReviewPriority = 1 | 2 | 3 | 4; // 1=critical, 4=low

export interface ReviewItemSummary {
  id: string;
  title: string;
  category: ReviewCategory;
  priority: ReviewPriority;
  status: ReviewStatus;
  created_at: string;
  assigned_to: string | null;
}

export interface ReviewItem extends ReviewItemSummary {
  description: string;
  context_data: Record<string, unknown>;
  engagement_id: string | null;
  created_by: string;
}

export interface ReviewStats {
  queued: number;
  in_review: number;
  completed_today: number;
  avg_review_time_minutes: number;
}

// ============================================================================
// Reviews API Functions
// ============================================================================

export async function getReviews(params?: {
  page?: number;
  page_size?: number;
  status?: ReviewStatus;
  category?: ReviewCategory;
}): Promise<PaginatedResponse<ReviewItemSummary>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.status) searchParams.set('status', params.status);
  if (params?.category) searchParams.set('category', params.category);
  return apiFetch(`/reviews?${searchParams}`);
}

export async function getReview(id: string): Promise<ReviewItem> {
  return apiFetch(`/reviews/${id}`);
}

export async function getReviewStats(): Promise<ReviewStats> {
  return apiFetch('/reviews/stats');
}

export async function completeReview(id: string, result: Record<string, unknown>): Promise<ReviewItem> {
  return apiFetch(`/reviews/${id}/complete`, {
    method: 'POST',
    body: JSON.stringify({ result }),
  });
}

export async function deferReview(id: string, reason: string): Promise<ReviewItem> {
  return apiFetch(`/reviews/${id}/defer`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function skipReview(id: string, reason: string): Promise<ReviewItem> {
  return apiFetch(`/reviews/${id}/skip`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

// ============================================================================
// Activity Types
// ============================================================================

export type ActivityType =
  | 'engagement_created'
  | 'engagement_started'
  | 'engagement_completed'
  | 'engagement_failed'
  | 'approval_requested'
  | 'approval_granted'
  | 'approval_rejected'
  | 'data_source_added'
  | 'data_source_connected'
  | 'agent_task_started'
  | 'agent_task_completed'
  | 'agent_message'
  | 'ontology_updated'
  | 'config_changed';

export interface ActivityItem {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp: string;
  user?: string;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Activity API Functions
// ============================================================================

export async function getEngagementActivities(
  engagementId: string,
  limit: number = 20
): Promise<{ items: ActivityItem[] }> {
  return apiFetch(`/engagements/${engagementId}/activities?limit=${limit}`);
}

export async function getRecentActivities(limit: number = 10): Promise<{ items: ActivityItem[] }> {
  return apiFetch(`/activities/recent?limit=${limit}`);
}

// ============================================================================
// Dashboard Metrics Types
// ============================================================================

export interface DashboardMetrics {
  activeEngagements: number;
  pendingApprovals: number;
  dataSources: number;
  completedThisMonth: number;
}

// ============================================================================
// Dashboard API Functions
// ============================================================================

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  return apiFetch('/dashboard/metrics');
}

// ============================================================================
// Observability Types (LangSmith Integration)
// ============================================================================

export interface TraceInfo {
  run_id: string;
  trace_id: string;
  name: string;
  start_time: string;
  end_time: string | null;
  status: 'success' | 'error' | 'running';
  engagement_id: string | null;
  agent_id: string | null;
  metadata: Record<string, unknown>;
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  error: string | null;
  latency_ms: number | null;
  token_usage: Record<string, number> | null;
}

export interface FeedbackCreate {
  run_id: string;
  score: number;
  comment?: string;
  key?: string;
}

export interface FeedbackResponse {
  run_id: string;
  score: number;
  comment: string | null;
  key: string;
  submitted_at: string;
  submitted_by: string;
}

export interface ObservabilityStats {
  total_traces: number;
  successful_traces: number;
  failed_traces: number;
  avg_latency_ms: number;
  total_tokens: number;
  feedback_count: number;
  avg_feedback_score: number | null;
  time_range_start: string | null;
  time_range_end: string | null;
  top_operations: Array<{ name: string; count: number }>;
  error_breakdown: Record<string, number>;
}

export interface DashboardUrlResponse {
  url: string;
  engagement_id: string | null;
  run_id: string | null;
}

export interface LangSmithHealth {
  status: 'healthy' | 'degraded' | 'unavailable';
  configured: boolean;
  enabled: boolean;
  connected: boolean;
  project?: string;
  endpoint?: string;
  error?: string;
}

// ============================================================================
// Observability API Functions
// ============================================================================

export async function getEngagementTraces(
  engagementId: string,
  params?: {
    page?: number;
    page_size?: number;
    status?: 'success' | 'error' | 'running';
    start_time?: string;
    end_time?: string;
  }
): Promise<PaginatedResponse<TraceInfo>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.status) searchParams.set('status', params.status);
  if (params?.start_time) searchParams.set('start_time', params.start_time);
  if (params?.end_time) searchParams.set('end_time', params.end_time);
  const query = searchParams.toString();
  return apiFetch(`/observability/traces/${engagementId}${query ? `?${query}` : ''}`);
}

export async function getAgentTraces(
  agentId: string,
  params?: {
    page?: number;
    page_size?: number;
    engagement_id?: string;
    start_time?: string;
    end_time?: string;
  }
): Promise<PaginatedResponse<TraceInfo>> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params?.engagement_id) searchParams.set('engagement_id', params.engagement_id);
  if (params?.start_time) searchParams.set('start_time', params.start_time);
  if (params?.end_time) searchParams.set('end_time', params.end_time);
  const query = searchParams.toString();
  return apiFetch(`/observability/traces/agent/${agentId}${query ? `?${query}` : ''}`);
}

export async function getTrace(runId: string): Promise<TraceInfo> {
  return apiFetch(`/observability/trace/${runId}`);
}

export async function submitFeedback(data: FeedbackCreate): Promise<FeedbackResponse> {
  return apiFetch('/observability/feedback', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getObservabilityStats(params?: {
  engagement_id?: string;
  start_time?: string;
  end_time?: string;
}): Promise<ObservabilityStats> {
  const searchParams = new URLSearchParams();
  if (params?.engagement_id) searchParams.set('engagement_id', params.engagement_id);
  if (params?.start_time) searchParams.set('start_time', params.start_time);
  if (params?.end_time) searchParams.set('end_time', params.end_time);
  const query = searchParams.toString();
  return apiFetch(`/observability/stats${query ? `?${query}` : ''}`);
}

export async function getDashboardUrl(params?: {
  engagement_id?: string;
  run_id?: string;
}): Promise<DashboardUrlResponse> {
  const searchParams = new URLSearchParams();
  if (params?.engagement_id) searchParams.set('engagement_id', params.engagement_id);
  if (params?.run_id) searchParams.set('run_id', params.run_id);
  const query = searchParams.toString();
  return apiFetch(`/observability/dashboard-url${query ? `?${query}` : ''}`);
}

export async function getLangSmithHealth(): Promise<LangSmithHealth> {
  return apiFetch('/observability/health');
}
