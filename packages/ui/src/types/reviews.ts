/**
 * Types for the review system - matching packages/human-interaction models
 */

// Review Status from human-interaction/review.py
export enum ReviewStatus {
  QUEUED = 'queued',
  IN_REVIEW = 'in_review',
  COMPLETED = 'completed',
  DEFERRED = 'deferred',
  SKIPPED = 'skipped',
}

// Review Priority (lower is higher priority)
export enum ReviewPriority {
  CRITICAL = 1,
  HIGH = 2,
  MEDIUM = 3,
  LOW = 4,
  BACKGROUND = 5,
}

// Review Category
export enum ReviewCategory {
  DATA_QUALITY = 'data_quality',
  AGENT_OUTPUT = 'agent_output',
  CONFIGURATION = 'configuration',
  MAPPING = 'mapping',
  ANOMALY = 'anomaly',
  COMPLIANCE = 'compliance',
}

// Review Item matching ReviewItem from human-interaction
export interface ReviewItem {
  id: string;
  engagement_id: string;
  category: ReviewCategory;
  title: string;
  description?: string;
  status: ReviewStatus;
  priority: ReviewPriority;
  created_at: string;
  assigned_to?: string;
  assigned_at?: string;
  completed_by?: string;
  completed_at?: string;
  review_data?: Record<string, unknown>;
  review_result?: ReviewResultData;
  batch_id?: string;
  source_type?: string;
  source_id?: string;
}

// Review Result
export interface ReviewResult {
  status: ReviewStatus;
  reviewer: string;
  comments?: string;
  corrections?: Record<string, unknown>;
  flags?: string[];
}

// Review Result Data (stored in review_result)
export interface ReviewResultData {
  status: string;
  comments?: string;
  corrections?: Record<string, unknown>;
  flags?: string[];
}

// Batch Review Result
export interface BatchReviewResult {
  batch_id: string;
  items_reviewed: number;
  items_accepted: number;
  items_rejected: number;
  items_deferred: number;
  reviewer: string;
  completed_at: string;
}

// Review Queue Stats
export interface ReviewQueueStats {
  total_queued: number;
  in_review: number;
  completed: number;
  deferred: number;
  skipped: number;
  by_priority: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    background: number;
  };
}

// Review filter options
export interface ReviewFilters {
  status?: ReviewStatus[];
  category?: ReviewCategory[];
  priority?: ReviewPriority[];
  engagement_id?: string;
  assigned_to?: string;
  batch_id?: string;
}

// UI-specific types

// Review list item (summary)
export interface ReviewListItem {
  id: string;
  title: string;
  category: ReviewCategory;
  status: ReviewStatus;
  priority: ReviewPriority;
  created_at: string;
  engagement_id: string;
  assigned_to?: string;
  batch_id?: string;
}

// Helper functions for display
export function getReviewStatusColor(status: ReviewStatus): string {
  switch (status) {
    case ReviewStatus.QUEUED:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
    case ReviewStatus.IN_REVIEW:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    case ReviewStatus.COMPLETED:
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    case ReviewStatus.DEFERRED:
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    case ReviewStatus.SKIPPED:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getPriorityColor(priority: ReviewPriority): string {
  switch (priority) {
    case ReviewPriority.CRITICAL:
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
    case ReviewPriority.HIGH:
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    case ReviewPriority.MEDIUM:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    case ReviewPriority.LOW:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
    case ReviewPriority.BACKGROUND:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getPriorityLabel(priority: ReviewPriority): string {
  switch (priority) {
    case ReviewPriority.CRITICAL:
      return 'Critical';
    case ReviewPriority.HIGH:
      return 'High';
    case ReviewPriority.MEDIUM:
      return 'Medium';
    case ReviewPriority.LOW:
      return 'Low';
    case ReviewPriority.BACKGROUND:
      return 'Background';
    default:
      return 'Unknown';
  }
}

export function getCategoryIcon(category: ReviewCategory): string {
  switch (category) {
    case ReviewCategory.DATA_QUALITY:
      return 'BarChart3';
    case ReviewCategory.AGENT_OUTPUT:
      return 'Bot';
    case ReviewCategory.CONFIGURATION:
      return 'Settings';
    case ReviewCategory.MAPPING:
      return 'GitMerge';
    case ReviewCategory.ANOMALY:
      return 'AlertTriangle';
    case ReviewCategory.COMPLIANCE:
      return 'Shield';
    default:
      return 'FileQuestion';
  }
}

export function getCategoryLabel(category: ReviewCategory): string {
  switch (category) {
    case ReviewCategory.DATA_QUALITY:
      return 'Data Quality';
    case ReviewCategory.AGENT_OUTPUT:
      return 'Agent Output';
    case ReviewCategory.CONFIGURATION:
      return 'Configuration';
    case ReviewCategory.MAPPING:
      return 'Mapping';
    case ReviewCategory.ANOMALY:
      return 'Anomaly';
    case ReviewCategory.COMPLIANCE:
      return 'Compliance';
    default:
      return 'Unknown';
  }
}
