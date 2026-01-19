/**
 * Types for the feedback system - matching packages/human-interaction models
 */

// Feedback Type from human-interaction/feedback.py
export enum FeedbackType {
  RATING = 'rating',
  CORRECTION = 'correction',
  SUGGESTION = 'suggestion',
  BUG_REPORT = 'bug_report',
  QUALITY_ASSESSMENT = 'quality_assessment',
  APPROVAL_FEEDBACK = 'approval_feedback',
}

// Feedback Category
export enum FeedbackCategory {
  AGENT_OUTPUT = 'agent_output',
  DATA_QUALITY = 'data_quality',
  MAPPING_ACCURACY = 'mapping_accuracy',
  RECOMMENDATION = 'recommendation',
  CLASSIFICATION = 'classification',
  UI_UX = 'ui_ux',
  PERFORMANCE = 'performance',
}

// Feedback Sentiment
export enum FeedbackSentiment {
  POSITIVE = 'positive',
  NEUTRAL = 'neutral',
  NEGATIVE = 'negative',
}

// Feedback Entry matching FeedbackEntry from human-interaction
export interface FeedbackEntry {
  id: string;
  engagement_id?: string;
  feedback_type: FeedbackType;
  category: FeedbackCategory;
  submitted_by: string;
  submitted_at: string;
  rating?: number;
  rating_scale_max: number;
  title?: string;
  description?: string;
  form_data?: Record<string, unknown>;
  corrections?: Record<string, unknown>;
  source_type?: string;
  source_id?: string;
  agent_name?: string;
  sentiment?: FeedbackSentiment;
  is_processed: boolean;
  processed_at?: string;
}

// Feedback Form Field
export interface FeedbackFormField {
  name: string;
  label: string;
  field_type: 'text' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'rating';
  required: boolean;
  options?: string[];
  default_value?: unknown;
  validation?: Record<string, unknown>;
}

// Feedback Form
export interface FeedbackForm {
  id: string;
  name: string;
  description?: string;
  feedback_type: FeedbackType;
  category: FeedbackCategory;
  fields: FeedbackFormField[];
  include_rating: boolean;
  include_comments: boolean;
}

// Feedback Summary
export interface FeedbackSummary {
  source_type: string;
  source_id: string;
  total_entries: number;
  average_rating?: number;
  sentiment_breakdown: {
    positive: number;
    neutral: number;
    negative: number;
  };
  category_breakdown: Record<string, number>;
  recent_entries: FeedbackEntry[];
}

// Agent Learning Signal
export interface AgentLearningSignal {
  agent_name: string;
  signal_type: 'correction' | 'preference' | 'quality_issue';
  context: Record<string, unknown>;
  corrections?: Record<string, unknown>;
  confidence: number;
  source_feedback_ids: string[];
  created_at: string;
}

// Feedback filter options
export interface FeedbackFilters {
  type?: FeedbackType[];
  category?: FeedbackCategory[];
  sentiment?: FeedbackSentiment[];
  engagement_id?: string;
  agent_name?: string;
  submitted_by?: string;
  is_processed?: boolean;
}

// Feedback stats
export interface FeedbackStats {
  total_entries: number;
  average_rating?: number;
  by_type: Record<FeedbackType, number>;
  by_category: Record<FeedbackCategory, number>;
  by_sentiment: Record<FeedbackSentiment, number>;
  unprocessed_count: number;
}

// UI-specific types

// Feedback list item (summary)
export interface FeedbackListItem {
  id: string;
  title?: string;
  feedback_type: FeedbackType;
  category: FeedbackCategory;
  submitted_by: string;
  submitted_at: string;
  rating?: number;
  sentiment?: FeedbackSentiment;
  engagement_id?: string;
  agent_name?: string;
}

// Submit feedback request
export interface SubmitFeedbackRequest {
  feedback_type: FeedbackType;
  category: FeedbackCategory;
  engagement_id?: string;
  rating?: number;
  title?: string;
  description?: string;
  form_data?: Record<string, unknown>;
  corrections?: Record<string, unknown>;
  source_type?: string;
  source_id?: string;
  agent_name?: string;
}

// Helper functions for display
export function getFeedbackTypeColor(type: FeedbackType): string {
  switch (type) {
    case FeedbackType.RATING:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
    case FeedbackType.CORRECTION:
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
    case FeedbackType.SUGGESTION:
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400';
    case FeedbackType.BUG_REPORT:
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
    case FeedbackType.QUALITY_ASSESSMENT:
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    case FeedbackType.APPROVAL_FEEDBACK:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getSentimentColor(sentiment: FeedbackSentiment): string {
  switch (sentiment) {
    case FeedbackSentiment.POSITIVE:
      return 'text-green-600 dark:text-green-400';
    case FeedbackSentiment.NEUTRAL:
      return 'text-gray-600 dark:text-gray-400';
    case FeedbackSentiment.NEGATIVE:
      return 'text-red-600 dark:text-red-400';
    default:
      return 'text-gray-600';
  }
}

export function getSentimentIcon(sentiment: FeedbackSentiment): string {
  switch (sentiment) {
    case FeedbackSentiment.POSITIVE:
      return 'ThumbsUp';
    case FeedbackSentiment.NEUTRAL:
      return 'Minus';
    case FeedbackSentiment.NEGATIVE:
      return 'ThumbsDown';
    default:
      return 'Minus';
  }
}

export function getFeedbackTypeIcon(type: FeedbackType): string {
  switch (type) {
    case FeedbackType.RATING:
      return 'Star';
    case FeedbackType.CORRECTION:
      return 'Edit';
    case FeedbackType.SUGGESTION:
      return 'Lightbulb';
    case FeedbackType.BUG_REPORT:
      return 'Bug';
    case FeedbackType.QUALITY_ASSESSMENT:
      return 'ClipboardCheck';
    case FeedbackType.APPROVAL_FEEDBACK:
      return 'CheckCircle';
    default:
      return 'MessageSquare';
  }
}

export function getFeedbackTypeLabel(type: FeedbackType): string {
  switch (type) {
    case FeedbackType.RATING:
      return 'Rating';
    case FeedbackType.CORRECTION:
      return 'Correction';
    case FeedbackType.SUGGESTION:
      return 'Suggestion';
    case FeedbackType.BUG_REPORT:
      return 'Bug Report';
    case FeedbackType.QUALITY_ASSESSMENT:
      return 'Quality Assessment';
    case FeedbackType.APPROVAL_FEEDBACK:
      return 'Approval Feedback';
    default:
      return 'Unknown';
  }
}

export function getCategoryLabel(category: FeedbackCategory): string {
  switch (category) {
    case FeedbackCategory.AGENT_OUTPUT:
      return 'Agent Output';
    case FeedbackCategory.DATA_QUALITY:
      return 'Data Quality';
    case FeedbackCategory.MAPPING_ACCURACY:
      return 'Mapping Accuracy';
    case FeedbackCategory.RECOMMENDATION:
      return 'Recommendation';
    case FeedbackCategory.CLASSIFICATION:
      return 'Classification';
    case FeedbackCategory.UI_UX:
      return 'UI/UX';
    case FeedbackCategory.PERFORMANCE:
      return 'Performance';
    default:
      return 'Unknown';
  }
}
