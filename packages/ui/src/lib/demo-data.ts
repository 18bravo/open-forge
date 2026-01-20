/**
 * Demo mode mock data
 * Realistic example data for showcasing the platform
 */

import type {
  EngagementSummary,
  Engagement,
  DataSourceSummary,
  DataSource,
  ApprovalRequestSummary,
  ApprovalRequest,
  ActivityItem,
  DashboardMetrics,
  AgentClusterSummary,
  AgentTaskSummary,
  AgentTask,
  PaginatedResponse,
} from './api';

// =============================================================================
// Engagements
// =============================================================================

export const demoEngagements: EngagementSummary[] = [
  {
    id: 'eng-001',
    name: 'Customer 360 Integration',
    status: 'in_progress',
    priority: 'high',
    created_by: 'sarah.chen@acme.com',
    created_at: '2026-01-15T09:00:00Z',
    updated_at: '2026-01-19T14:30:00Z',
  },
  {
    id: 'eng-002',
    name: 'Quarterly Revenue Pipeline',
    status: 'completed',
    priority: 'critical',
    created_by: 'mike.johnson@acme.com',
    created_at: '2026-01-10T08:00:00Z',
    updated_at: '2026-01-18T16:45:00Z',
  },
  {
    id: 'eng-003',
    name: 'Product Catalog Sync',
    status: 'pending_approval',
    priority: 'medium',
    created_by: 'lisa.wong@acme.com',
    created_at: '2026-01-17T11:00:00Z',
    updated_at: '2026-01-19T10:15:00Z',
  },
  {
    id: 'eng-004',
    name: 'Marketing Attribution Model',
    status: 'draft',
    priority: 'low',
    created_by: 'david.kim@acme.com',
    created_at: '2026-01-19T08:00:00Z',
    updated_at: '2026-01-19T08:00:00Z',
  },
  {
    id: 'eng-005',
    name: 'Supply Chain Analytics',
    status: 'in_progress',
    priority: 'high',
    created_by: 'sarah.chen@acme.com',
    created_at: '2026-01-12T10:00:00Z',
    updated_at: '2026-01-19T12:00:00Z',
  },
];

export const demoEngagementDetails: Record<string, Engagement> = {
  'eng-001': {
    id: 'eng-001',
    name: 'Customer 360 Integration',
    description: 'Consolidate customer data from multiple sources to create a unified customer view for the sales and support teams.',
    objective: 'Create a single source of truth for customer data by integrating Salesforce CRM, PostgreSQL transactional database, and Snowflake analytics warehouse.',
    status: 'in_progress',
    priority: 'high',
    data_sources: [
      { source_id: 'ds-001', source_type: 'postgresql', access_mode: 'read' },
      { source_id: 'ds-002', source_type: 'api', access_mode: 'read' },
      { source_id: 'ds-003', source_type: 'snowflake', access_mode: 'read_write' },
    ],
    agent_config: {
      max_iterations: 50,
      timeout_minutes: 30,
      clusters: ['data-integration', 'quality-assurance'],
    },
    tags: ['customer-data', 'integration', 'high-priority'],
    metadata: { estimated_records: 2500000, target_completion: '2026-01-25' },
    requires_approval: true,
    created_by: 'sarah.chen@acme.com',
    created_at: '2026-01-15T09:00:00Z',
    updated_at: '2026-01-19T14:30:00Z',
    started_at: '2026-01-15T10:00:00Z',
  },
  'eng-002': {
    id: 'eng-002',
    name: 'Quarterly Revenue Pipeline',
    description: 'Automated quarterly revenue reporting pipeline that aggregates data from all business units.',
    objective: 'Generate accurate Q4 2025 revenue reports by aggregating sales data, subscriptions, and service revenue.',
    status: 'completed',
    priority: 'critical',
    data_sources: [
      { source_id: 'ds-001', source_type: 'postgresql', access_mode: 'read' },
      { source_id: 'ds-003', source_type: 'snowflake', access_mode: 'read_write' },
    ],
    agent_config: { max_iterations: 100, timeout_minutes: 60 },
    tags: ['finance', 'reporting', 'quarterly'],
    metadata: { report_period: 'Q4-2025', generated_reports: 12 },
    requires_approval: true,
    created_by: 'mike.johnson@acme.com',
    created_at: '2026-01-10T08:00:00Z',
    updated_at: '2026-01-18T16:45:00Z',
    started_at: '2026-01-10T09:00:00Z',
    completed_at: '2026-01-18T16:45:00Z',
  },
  'eng-003': {
    id: 'eng-003',
    name: 'Product Catalog Sync',
    description: 'Synchronize product catalog across e-commerce platform, ERP system, and marketing tools.',
    objective: 'Ensure product information consistency across all systems with real-time sync capabilities.',
    status: 'pending_approval',
    priority: 'medium',
    data_sources: [
      { source_id: 'ds-001', source_type: 'postgresql', access_mode: 'read_write' },
      { source_id: 'ds-004', source_type: 's3', access_mode: 'read' },
    ],
    agent_config: { max_iterations: 30, timeout_minutes: 15 },
    tags: ['product', 'sync', 'e-commerce'],
    metadata: { product_count: 15000 },
    requires_approval: true,
    created_by: 'lisa.wong@acme.com',
    created_at: '2026-01-17T11:00:00Z',
    updated_at: '2026-01-19T10:15:00Z',
  },
};

// =============================================================================
// Data Sources
// =============================================================================

export const demoDataSources: DataSourceSummary[] = [
  {
    id: 'ds-001',
    name: 'Acme Production DB',
    source_type: 'postgresql',
    status: 'active',
    created_at: '2026-01-05T08:00:00Z',
  },
  {
    id: 'ds-002',
    name: 'Salesforce CRM',
    source_type: 'api',
    status: 'active',
    created_at: '2026-01-06T10:00:00Z',
  },
  {
    id: 'ds-003',
    name: 'Snowflake Analytics',
    source_type: 'iceberg',
    status: 'active',
    created_at: '2026-01-07T09:00:00Z',
  },
  {
    id: 'ds-004',
    name: 'S3 Data Lake',
    source_type: 's3',
    status: 'active',
    created_at: '2026-01-08T11:00:00Z',
  },
  {
    id: 'ds-005',
    name: 'Kafka Event Stream',
    source_type: 'kafka',
    status: 'active',
    created_at: '2026-01-09T14:00:00Z',
  },
];

export const demoDataSourceDetails: Record<string, DataSource> = {
  'ds-001': {
    id: 'ds-001',
    name: 'Acme Production DB',
    description: 'Primary PostgreSQL database for transactional data',
    source_type: 'postgresql',
    status: 'active',
    connection_config: {
      host: 'prod-db.acme.internal',
      port: 5432,
      database: 'acme_prod',
      ssl: true,
    },
    schema_config: { schemas: ['public', 'sales', 'customers'] },
    tags: ['production', 'postgresql', 'primary'],
    metadata: { table_count: 156, estimated_size_gb: 450 },
    created_by: 'admin@acme.com',
    created_at: '2026-01-05T08:00:00Z',
    updated_at: '2026-01-19T06:00:00Z',
    last_tested_at: '2026-01-19T06:00:00Z',
  },
};

// =============================================================================
// Approvals
// =============================================================================

export const demoApprovals: ApprovalRequestSummary[] = [
  {
    id: 'apr-001',
    approval_type: 'schema_change',
    status: 'pending',
    title: 'Add customer_segment column to customers table',
    resource_id: 'ds-001',
    requested_by: 'sarah.chen@acme.com',
    requested_at: '2026-01-19T13:00:00Z',
    expires_at: '2026-01-20T13:00:00Z',
  },
  {
    id: 'apr-002',
    approval_type: 'tool_execution',
    status: 'pending',
    title: 'Execute bulk data migration for Customer 360',
    resource_id: 'eng-001',
    requested_by: 'data-integration-agent',
    requested_at: '2026-01-19T14:00:00Z',
    expires_at: '2026-01-19T20:00:00Z',
  },
  {
    id: 'apr-003',
    approval_type: 'engagement',
    status: 'approved',
    title: 'Start Product Catalog Sync engagement',
    resource_id: 'eng-003',
    requested_by: 'lisa.wong@acme.com',
    requested_at: '2026-01-18T15:00:00Z',
  },
];

export const demoApprovalDetails: Record<string, ApprovalRequest> = {
  'apr-001': {
    id: 'apr-001',
    approval_type: 'schema_change',
    status: 'pending',
    title: 'Add customer_segment column to customers table',
    description: 'Add a new VARCHAR(50) column to store customer segmentation data derived from the Customer 360 analysis.',
    resource_id: 'ds-001',
    resource_type: 'data_source',
    requested_by: 'sarah.chen@acme.com',
    requested_at: '2026-01-19T13:00:00Z',
    details: {
      table: 'customers',
      column_name: 'customer_segment',
      column_type: 'VARCHAR(50)',
      nullable: true,
      default_value: null,
    },
    expires_at: '2026-01-20T13:00:00Z',
  },
  'apr-002': {
    id: 'apr-002',
    approval_type: 'tool_execution',
    status: 'pending',
    title: 'Execute bulk data migration for Customer 360',
    description: 'The data integration agent requests permission to execute a bulk INSERT operation to migrate 50,000 customer records.',
    resource_id: 'eng-001',
    resource_type: 'engagement',
    requested_by: 'data-integration-agent',
    requested_at: '2026-01-19T14:00:00Z',
    details: {
      operation: 'BULK_INSERT',
      target_table: 'unified_customers',
      record_count: 50000,
      estimated_duration_seconds: 120,
    },
    expires_at: '2026-01-19T20:00:00Z',
  },
};

// =============================================================================
// Activities
// =============================================================================

export const demoActivities: ActivityItem[] = [
  {
    id: 'act-001',
    type: 'agent_task_completed',
    title: 'Data validation completed',
    description: 'Quality assurance agent validated 25,000 customer records',
    timestamp: '2026-01-19T14:25:00Z',
    user: 'qa-agent',
    metadata: { engagement_id: 'eng-001', records_validated: 25000 },
  },
  {
    id: 'act-002',
    type: 'approval_requested',
    title: 'Schema change approval requested',
    description: 'Request to add customer_segment column',
    timestamp: '2026-01-19T13:00:00Z',
    user: 'sarah.chen@acme.com',
    metadata: { approval_id: 'apr-001' },
  },
  {
    id: 'act-003',
    type: 'engagement_started',
    title: 'Supply Chain Analytics started',
    description: 'Engagement eng-005 has begun processing',
    timestamp: '2026-01-19T12:00:00Z',
    user: 'sarah.chen@acme.com',
    metadata: { engagement_id: 'eng-005' },
  },
  {
    id: 'act-004',
    type: 'data_source_connected',
    title: 'Kafka Event Stream connected',
    description: 'Successfully established connection to Kafka cluster',
    timestamp: '2026-01-19T10:30:00Z',
    user: 'admin@acme.com',
    metadata: { data_source_id: 'ds-005' },
  },
  {
    id: 'act-005',
    type: 'engagement_completed',
    title: 'Quarterly Revenue Pipeline completed',
    description: 'All Q4 2025 revenue reports generated successfully',
    timestamp: '2026-01-18T16:45:00Z',
    user: 'system',
    metadata: { engagement_id: 'eng-002' },
  },
];

// =============================================================================
// Dashboard Metrics
// =============================================================================

export const demoDashboardMetrics: DashboardMetrics = {
  activeEngagements: 2,
  pendingApprovals: 2,
  dataSources: 5,
  completedThisMonth: 12,
};

// =============================================================================
// Agent Clusters
// =============================================================================

export const demoAgentClusters: AgentClusterSummary[] = [
  {
    id: 'cluster-001',
    name: 'Data Integration',
    slug: 'data-integration',
    status: 'running',
    instance_count: 3,
    max_instances: 5,
    cpu_usage: 45,
    memory_usage: 62,
    queued_tasks: 2,
  },
  {
    id: 'cluster-002',
    name: 'Quality Assurance',
    slug: 'quality-assurance',
    status: 'running',
    instance_count: 2,
    max_instances: 4,
    cpu_usage: 30,
    memory_usage: 45,
    queued_tasks: 0,
  },
  {
    id: 'cluster-003',
    name: 'Code Generation',
    slug: 'code-generation',
    status: 'idle',
    instance_count: 1,
    max_instances: 3,
    cpu_usage: 5,
    memory_usage: 20,
    queued_tasks: 0,
  },
];

export const demoAgentTasks: AgentTaskSummary[] = [
  {
    id: 'task-001',
    engagement_id: 'eng-001',
    task_type: 'data_extraction',
    status: 'running',
    current_iteration: 15,
    created_at: '2026-01-19T14:00:00Z',
  },
  {
    id: 'task-002',
    engagement_id: 'eng-001',
    task_type: 'data_validation',
    status: 'completed',
    current_iteration: 8,
    created_at: '2026-01-19T13:30:00Z',
    completed_at: '2026-01-19T14:25:00Z',
  },
  {
    id: 'task-003',
    engagement_id: 'eng-005',
    task_type: 'schema_mapping',
    status: 'waiting_approval',
    current_iteration: 3,
    created_at: '2026-01-19T12:15:00Z',
  },
];

export const demoAgentTaskDetails: Record<string, AgentTask> = {
  'task-001': {
    id: 'task-001',
    engagement_id: 'eng-001',
    task_type: 'data_extraction',
    description: 'Extract customer records from PostgreSQL and Salesforce',
    status: 'running',
    tools: ['sql_query', 'api_fetch', 'data_transform'],
    max_iterations: 50,
    current_iteration: 15,
    timeout_seconds: 1800,
    messages: [
      {
        id: 'msg-001',
        role: 'system',
        content: 'Starting data extraction task for Customer 360 Integration',
        timestamp: '2026-01-19T14:00:00Z',
      },
      {
        id: 'msg-002',
        role: 'assistant',
        content: 'Connecting to PostgreSQL database to extract customer records...',
        timestamp: '2026-01-19T14:00:30Z',
      },
      {
        id: 'msg-003',
        role: 'assistant',
        content: 'Successfully extracted 25,000 records from customers table. Now fetching Salesforce data...',
        timestamp: '2026-01-19T14:05:00Z',
        tool_calls: [
          {
            id: 'tc-001',
            name: 'sql_query',
            arguments: { query: 'SELECT * FROM customers WHERE updated_at > :last_sync', limit: 50000 },
            result: { rows_returned: 25000, execution_time_ms: 1250 },
            status: 'completed',
            duration_ms: 1250,
          },
        ],
      },
    ],
    pending_tool_approvals: [],
    created_at: '2026-01-19T14:00:00Z',
    started_at: '2026-01-19T14:00:00Z',
  },
  'task-002': {
    id: 'task-002',
    engagement_id: 'eng-001',
    task_type: 'data_validation',
    description: 'Validate extracted customer data for quality and completeness',
    status: 'completed',
    tools: ['schema_validator', 'null_checker', 'duplicate_detector'],
    max_iterations: 20,
    current_iteration: 8,
    timeout_seconds: 900,
    messages: [
      {
        id: 'msg-004',
        role: 'system',
        content: 'Starting data validation task',
        timestamp: '2026-01-19T13:30:00Z',
      },
      {
        id: 'msg-005',
        role: 'assistant',
        content: 'Validation complete. Found 98.5% data quality score with 375 records requiring attention.',
        timestamp: '2026-01-19T14:25:00Z',
      },
    ],
    pending_tool_approvals: [],
    created_at: '2026-01-19T13:30:00Z',
    started_at: '2026-01-19T13:30:00Z',
    completed_at: '2026-01-19T14:25:00Z',
  },
  'task-003': {
    id: 'task-003',
    engagement_id: 'eng-005',
    task_type: 'schema_mapping',
    description: 'Map source schema to target ontology for Supply Chain Analytics',
    status: 'waiting_approval',
    tools: ['schema_analyzer', 'ontology_mapper', 'transform_generator'],
    max_iterations: 30,
    current_iteration: 3,
    timeout_seconds: 1200,
    messages: [
      {
        id: 'msg-006',
        role: 'system',
        content: 'Starting schema mapping task',
        timestamp: '2026-01-19T12:15:00Z',
      },
      {
        id: 'msg-007',
        role: 'assistant',
        content: 'Requesting approval to modify target schema with proposed mappings.',
        timestamp: '2026-01-19T12:30:00Z',
      },
    ],
    pending_tool_approvals: [
      {
        id: 'tc-002',
        name: 'schema_modify',
        arguments: { table: 'supply_chain_entities', add_columns: ['supplier_rating', 'lead_time_days'] },
        status: 'pending',
      },
    ],
    created_at: '2026-01-19T12:15:00Z',
    started_at: '2026-01-19T12:15:00Z',
  },
};

// =============================================================================
// Helper to create paginated responses
// =============================================================================

export function paginateDemo<T>(
  items: T[],
  page: number = 1,
  pageSize: number = 10
): PaginatedResponse<T> {
  const start = (page - 1) * pageSize;
  const paginatedItems = items.slice(start, start + pageSize);
  return {
    items: paginatedItems,
    total: items.length,
    page,
    page_size: pageSize,
    total_pages: Math.ceil(items.length / pageSize),
  };
}
