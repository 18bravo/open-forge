/**
 * Types for the approval system - matching packages/human-interaction models
 */

// Approval Status from human-interaction/approvals.py
export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  ESCALATED = 'escalated',
}

// Approval Type from human-interaction/approvals.py
export enum ApprovalType {
  AGENT_ACTION = 'agent_action',
  DATA_CHANGE = 'data_change',
  CONFIGURATION = 'configuration',
  DEPLOYMENT = 'deployment',
  ACCESS_GRANT = 'access_grant',
  // API router types
  ENGAGEMENT = 'engagement',
  TOOL_EXECUTION = 'tool_execution',
  DATA_ACCESS = 'data_access',
  SCHEMA_CHANGE = 'schema_change',
}

// Escalation levels
export type EscalationLevel = 'level_1' | 'level_2' | 'level_3' | 'executive';

// Approval Request matching ApprovalRequest from human-interaction
export interface ApprovalRequest {
  id: string;
  engagement_id: string;
  approval_type: ApprovalType;
  title: string;
  description?: string;
  status: ApprovalStatus;
  requested_by: string;
  requested_at: string;
  deadline?: string;
  decided_by?: string;
  decided_at?: string;
  decision_comments?: string;
  context_data?: Record<string, unknown>;
  escalation_level: EscalationLevel;
  // Extended fields from API
  resource_id?: string;
  resource_type?: string;
  details?: Record<string, unknown>;
  expires_at?: string;
  rejection_reason?: string;
}

// Approval Decision
export interface ApprovalDecision {
  approved: boolean;
  decided_by: string;
  comments?: string;
  modifications?: Record<string, unknown>;
  conditions?: Record<string, unknown>;
}

// Approval Policy from API
export interface ApprovalPolicy {
  id: string;
  name: string;
  description?: string;
  approval_type: ApprovalType;
  rules: Record<string, unknown>;
  required_approvers: number;
  auto_approve_conditions?: Record<string, unknown>;
  expiration_hours: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// UI-specific types

// Priority for sorting and display
export enum ApprovalPriority {
  CRITICAL = 1,
  HIGH = 2,
  MEDIUM = 3,
  LOW = 4,
}

// Approval filter options
export interface ApprovalFilters {
  status?: ApprovalStatus[];
  type?: ApprovalType[];
  priority?: ApprovalPriority[];
  engagement_id?: string;
  requested_by?: string;
  deadline_before?: string;
  escalation_level?: EscalationLevel[];
}

// Approval list item (summary)
export interface ApprovalListItem {
  id: string;
  title: string;
  approval_type: ApprovalType;
  status: ApprovalStatus;
  requested_by: string;
  requested_at: string;
  deadline?: string;
  escalation_level: EscalationLevel;
  engagement_id: string;
  has_urgency: boolean;
}

// Batch action types
export type BatchAction = 'approve' | 'reject' | 'escalate';

export interface BatchActionRequest {
  approval_ids: string[];
  action: BatchAction;
  comments?: string;
}

// Approval stats for inbox
export interface ApprovalStats {
  total_pending: number;
  urgent_count: number;
  expiring_soon: number;
  by_type: Record<ApprovalType, number>;
  by_status: Record<ApprovalStatus, number>;
}

// Helper functions for display
export function getApprovalStatusColor(status: ApprovalStatus): string {
  switch (status) {
    case ApprovalStatus.PENDING:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    case ApprovalStatus.APPROVED:
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    case ApprovalStatus.REJECTED:
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
    case ApprovalStatus.EXPIRED:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    case ApprovalStatus.ESCALATED:
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getApprovalTypeIcon(type: ApprovalType): string {
  switch (type) {
    case ApprovalType.AGENT_ACTION:
      return 'Bot';
    case ApprovalType.DATA_CHANGE:
      return 'Database';
    case ApprovalType.CONFIGURATION:
      return 'Settings';
    case ApprovalType.DEPLOYMENT:
      return 'Rocket';
    case ApprovalType.ACCESS_GRANT:
      return 'Key';
    case ApprovalType.ENGAGEMENT:
      return 'Users';
    case ApprovalType.TOOL_EXECUTION:
      return 'Terminal';
    case ApprovalType.DATA_ACCESS:
      return 'Eye';
    case ApprovalType.SCHEMA_CHANGE:
      return 'Table';
    default:
      return 'FileQuestion';
  }
}

export function getApprovalTypeLabel(type: ApprovalType): string {
  switch (type) {
    case ApprovalType.AGENT_ACTION:
      return 'Agent Action';
    case ApprovalType.DATA_CHANGE:
      return 'Data Change';
    case ApprovalType.CONFIGURATION:
      return 'Configuration';
    case ApprovalType.DEPLOYMENT:
      return 'Deployment';
    case ApprovalType.ACCESS_GRANT:
      return 'Access Grant';
    case ApprovalType.ENGAGEMENT:
      return 'Engagement';
    case ApprovalType.TOOL_EXECUTION:
      return 'Tool Execution';
    case ApprovalType.DATA_ACCESS:
      return 'Data Access';
    case ApprovalType.SCHEMA_CHANGE:
      return 'Schema Change';
    default:
      return 'Unknown';
  }
}

export function isUrgent(approval: ApprovalRequest | ApprovalListItem): boolean {
  if (!approval.deadline) return false;
  const deadline = new Date(approval.deadline);
  const now = new Date();
  const hoursUntilDeadline = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60);
  return hoursUntilDeadline <= 4 && hoursUntilDeadline > 0;
}

export function isExpiringSoon(approval: ApprovalRequest | ApprovalListItem): boolean {
  if (!approval.deadline) return false;
  const deadline = new Date(approval.deadline);
  const now = new Date();
  const hoursUntilDeadline = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60);
  return hoursUntilDeadline <= 24 && hoursUntilDeadline > 0;
}
