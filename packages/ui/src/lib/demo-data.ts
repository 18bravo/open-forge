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
  AgentClusterDetail,
  AgentTypeSummary,
  AgentTaskSummary,
  AgentTask,
  PaginatedResponse,
  PipelineSummary,
  PipelineDetail,
  PipelineRunSummary,
  SystemSettings,
  ConnectorSummary,
  UserSummary,
  AuditLogEntry,
  ReviewItemSummary,
  ReviewItem,
  ReviewStats,
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
// Admin System Health
// =============================================================================

export const demoSystemHealth = {
  services: [
    { service: 'API Server', status: 'healthy' as const, latency: 45, uptime: 99.98 },
    { service: 'Database (PostgreSQL)', status: 'healthy' as const, latency: 12, uptime: 99.99 },
    { service: 'Cache (Redis)', status: 'healthy' as const, latency: 2, uptime: 99.95 },
    { service: 'Message Queue (Kafka)', status: 'healthy' as const, latency: 8, uptime: 99.97 },
    { service: 'Agent Orchestrator', status: 'healthy' as const, latency: 23, uptime: 99.92 },
    { service: 'ML Pipeline Service', status: 'degraded' as const, latency: 450, uptime: 98.50 },
  ],
  overall_status: 'degraded' as const,
  timestamp: '2026-01-19T14:30:00Z',
};

export const demoAdminDashboardStats = {
  system_health: { healthy: 5, degraded: 1, unhealthy: 0 },
  engagements: { total: 5, active: 2, pending: 1, completed: 2 },
  agents: { total_clusters: 3, running_instances: 6, queued_tasks: 2 },
  approvals: { pending: 2, approved_today: 5, rejected_today: 1 },
};

export const demoAlerts = [
  {
    id: 'alert-001',
    severity: 'warning' as const,
    message: 'ML Pipeline Service experiencing high latency (450ms)',
    timestamp: '2026-01-19T14:25:00Z',
    source: 'Health Monitor',
  },
  {
    id: 'alert-002',
    severity: 'info' as const,
    message: 'Customer 360 Integration task completed successfully',
    timestamp: '2026-01-19T14:20:00Z',
    source: 'Agent Orchestrator',
  },
  {
    id: 'alert-003',
    severity: 'warning' as const,
    message: 'Approval request apr-002 expiring in 6 hours',
    timestamp: '2026-01-19T14:00:00Z',
    source: 'Approval Service',
  },
  {
    id: 'alert-004',
    severity: 'info' as const,
    message: 'New data source "Kafka Event Stream" connected',
    timestamp: '2026-01-19T10:30:00Z',
    source: 'Connector Service',
  },
];

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

export const demoAgentClusterDetails: Record<string, AgentClusterDetail> = {
  'data-integration': {
    id: 'cluster-001',
    name: 'Data Integration',
    slug: 'data-integration',
    status: 'running',
    instance_count: 3,
    max_instances: 5,
    cpu_usage: 45,
    memory_usage: 62,
    queued_tasks: 2,
    description: 'Handles data extraction, transformation, and loading from various data sources.',
    agent_types: ['schema_discovery', 'data_extraction', 'data_validation'],
    config: {
      min_instances: 1,
      max_instances: 5,
      auto_scale: true,
      scale_up_threshold: 70,
      scale_down_threshold: 30,
    },
    instances: [
      { id: 'inst-001', name: 'data-integration-1', status: 'running', current_task: 'Extracting customer data', started_at: '2026-01-19T08:00:00Z', cpu_usage: 65, memory_usage: 72 },
      { id: 'inst-002', name: 'data-integration-2', status: 'running', current_task: 'Validating schema mappings', started_at: '2026-01-19T08:00:00Z', cpu_usage: 45, memory_usage: 58 },
      { id: 'inst-003', name: 'data-integration-3', status: 'idle', current_task: null, started_at: '2026-01-19T10:30:00Z', cpu_usage: 5, memory_usage: 25 },
    ],
  },
  'quality-assurance': {
    id: 'cluster-002',
    name: 'Quality Assurance',
    slug: 'quality-assurance',
    status: 'running',
    instance_count: 2,
    max_instances: 4,
    cpu_usage: 30,
    memory_usage: 45,
    queued_tasks: 0,
    description: 'Runs data quality checks, validation rules, and anomaly detection.',
    agent_types: ['data_quality', 'anomaly_detection'],
    config: {
      min_instances: 1,
      max_instances: 4,
      auto_scale: true,
      scale_up_threshold: 80,
      scale_down_threshold: 20,
    },
    instances: [
      { id: 'inst-004', name: 'qa-agent-1', status: 'running', current_task: 'Running quality checks', started_at: '2026-01-19T09:00:00Z', cpu_usage: 40, memory_usage: 50 },
      { id: 'inst-005', name: 'qa-agent-2', status: 'idle', current_task: null, started_at: '2026-01-19T09:00:00Z', cpu_usage: 10, memory_usage: 35 },
    ],
  },
  'code-generation': {
    id: 'cluster-003',
    name: 'Code Generation',
    slug: 'code-generation',
    status: 'idle',
    instance_count: 1,
    max_instances: 3,
    cpu_usage: 5,
    memory_usage: 20,
    queued_tasks: 0,
    description: 'Generates code, reports, and documentation from ontology definitions.',
    agent_types: ['code_gen', 'report_gen', 'doc_gen'],
    config: {
      min_instances: 0,
      max_instances: 3,
      auto_scale: false,
      scale_up_threshold: 90,
      scale_down_threshold: 10,
    },
    instances: [
      { id: 'inst-006', name: 'codegen-1', status: 'idle', current_task: null, started_at: '2026-01-19T12:00:00Z', cpu_usage: 5, memory_usage: 20 },
    ],
  },
  // Also add discovery, data-architect, app-builder to match agent types
  'discovery': {
    id: 'cluster-004',
    name: 'Discovery',
    slug: 'discovery',
    status: 'running',
    instance_count: 2,
    max_instances: 4,
    cpu_usage: 55,
    memory_usage: 48,
    queued_tasks: 1,
    description: 'Discovers and profiles data sources, schemas, and relationships.',
    agent_types: ['schema_discovery', 'data_quality'],
    config: {
      min_instances: 1,
      max_instances: 4,
      auto_scale: true,
      scale_up_threshold: 75,
      scale_down_threshold: 25,
    },
    instances: [
      { id: 'inst-007', name: 'discovery-1', status: 'running', current_task: 'Profiling PostgreSQL schema', started_at: '2026-01-19T07:00:00Z', cpu_usage: 70, memory_usage: 55 },
      { id: 'inst-008', name: 'discovery-2', status: 'running', current_task: 'Analyzing data quality', started_at: '2026-01-19T07:30:00Z', cpu_usage: 40, memory_usage: 42 },
    ],
  },
  'data-architect': {
    id: 'cluster-005',
    name: 'Data Architect',
    slug: 'data-architect',
    status: 'running',
    instance_count: 2,
    max_instances: 3,
    cpu_usage: 35,
    memory_usage: 52,
    queued_tasks: 0,
    description: 'Builds and maintains ontologies, schema mappings, and data models.',
    agent_types: ['ontology_build', 'schema_mapping'],
    config: {
      min_instances: 1,
      max_instances: 3,
      auto_scale: true,
      scale_up_threshold: 80,
      scale_down_threshold: 30,
    },
    instances: [
      { id: 'inst-009', name: 'architect-1', status: 'running', current_task: 'Building customer ontology', started_at: '2026-01-19T06:00:00Z', cpu_usage: 50, memory_usage: 60 },
      { id: 'inst-010', name: 'architect-2', status: 'idle', current_task: null, started_at: '2026-01-19T08:00:00Z', cpu_usage: 20, memory_usage: 44 },
    ],
  },
  'app-builder': {
    id: 'cluster-006',
    name: 'App Builder',
    slug: 'app-builder',
    status: 'idle',
    instance_count: 1,
    max_instances: 2,
    cpu_usage: 8,
    memory_usage: 22,
    queued_tasks: 0,
    description: 'Generates applications, reports, and dashboards from ontology.',
    agent_types: ['app_generation', 'report_generation'],
    config: {
      min_instances: 0,
      max_instances: 2,
      auto_scale: false,
      scale_up_threshold: 85,
      scale_down_threshold: 15,
    },
    instances: [
      { id: 'inst-011', name: 'appbuilder-1', status: 'idle', current_task: null, started_at: '2026-01-19T11:00:00Z', cpu_usage: 8, memory_usage: 22 },
    ],
  },
};

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
// Agent Types
// =============================================================================

export const demoAgentTypes: AgentTypeSummary[] = [
  {
    id: 'agent-type-001',
    name: 'Schema Discovery Agent',
    cluster: 'discovery',
    status: 'active',
    task_type: 'schema_discovery',
    version: '2.1.0',
    instance_count: 2,
  },
  {
    id: 'agent-type-002',
    name: 'Data Quality Agent',
    cluster: 'discovery',
    status: 'active',
    task_type: 'data_quality',
    version: '1.8.2',
    instance_count: 2,
  },
  {
    id: 'agent-type-003',
    name: 'Ontology Builder Agent',
    cluster: 'data-architect',
    status: 'active',
    task_type: 'ontology_build',
    version: '3.0.1',
    instance_count: 1,
  },
  {
    id: 'agent-type-004',
    name: 'Schema Mapping Agent',
    cluster: 'data-architect',
    status: 'active',
    task_type: 'schema_mapping',
    version: '2.4.0',
    instance_count: 2,
  },
  {
    id: 'agent-type-005',
    name: 'App Builder Agent',
    cluster: 'app-builder',
    status: 'inactive',
    task_type: 'app_generation',
    version: '1.2.0',
    instance_count: 0,
  },
  {
    id: 'agent-type-006',
    name: 'Report Generator Agent',
    cluster: 'app-builder',
    status: 'active',
    task_type: 'report_generation',
    version: '1.5.3',
    instance_count: 1,
  },
];

// =============================================================================
// Pipelines
// =============================================================================

export const demoPipelines: PipelineSummary[] = [
  {
    id: 'pipeline-001',
    name: 'Customer Data Sync',
    description: 'Daily sync of customer data from CRM to data warehouse',
    status: 'active',
    schedule: '0 2 * * *',
    last_run: '2026-01-19T02:00:00Z',
    last_run_status: 'completed',
    next_run: '2026-01-20T02:00:00Z',
  },
  {
    id: 'pipeline-002',
    name: 'Product Catalog Update',
    description: 'Hourly product inventory and pricing sync',
    status: 'active',
    schedule: '0 * * * *',
    last_run: '2026-01-19T14:00:00Z',
    last_run_status: 'completed',
    next_run: '2026-01-19T15:00:00Z',
  },
  {
    id: 'pipeline-003',
    name: 'Analytics ETL',
    description: 'Transform and load analytics data for reporting',
    status: 'paused',
    schedule: '0 4 * * *',
    last_run: '2026-01-18T04:00:00Z',
    last_run_status: 'failed',
    next_run: null,
  },
  {
    id: 'pipeline-004',
    name: 'ML Model Refresh',
    description: 'Retrain recommendation models with latest data',
    status: 'active',
    schedule: '0 0 * * 0',
    last_run: '2026-01-14T00:00:00Z',
    last_run_status: 'completed',
    next_run: '2026-01-21T00:00:00Z',
  },
];

export const demoPipelineDetails: Record<string, PipelineDetail> = {
  'pipeline-001': {
    id: 'pipeline-001',
    name: 'Customer Data Sync',
    description: 'Daily sync of customer data from CRM to data warehouse',
    status: 'active',
    schedule: '0 2 * * *',
    last_run: '2026-01-19T02:00:00Z',
    last_run_status: 'completed',
    next_run: '2026-01-20T02:00:00Z',
    created_at: '2025-06-15T10:00:00Z',
    updated_at: '2026-01-19T02:45:00Z',
    config: {
      schedule: '0 2 * * *',
      timeout_minutes: 60,
      max_retries: 3,
      concurrency: 2,
    },
    stages: [
      { id: 'stage-001', name: 'Extract from CRM', order: 1, type: 'extract' },
      { id: 'stage-002', name: 'Transform Data', order: 2, type: 'transform' },
      { id: 'stage-003', name: 'Validate Schema', order: 3, type: 'validate' },
      { id: 'stage-004', name: 'Load to Warehouse', order: 4, type: 'load' },
    ],
  },
  'pipeline-002': {
    id: 'pipeline-002',
    name: 'Product Catalog Update',
    description: 'Hourly product inventory and pricing sync',
    status: 'active',
    schedule: '0 * * * *',
    last_run: '2026-01-19T14:00:00Z',
    last_run_status: 'completed',
    next_run: '2026-01-19T15:00:00Z',
    created_at: '2025-08-01T08:00:00Z',
    updated_at: '2026-01-19T14:15:00Z',
    config: {
      schedule: '0 * * * *',
      timeout_minutes: 30,
      max_retries: 2,
      concurrency: 1,
    },
    stages: [
      { id: 'stage-005', name: 'Fetch Product Data', order: 1, type: 'extract' },
      { id: 'stage-006', name: 'Update Prices', order: 2, type: 'transform' },
      { id: 'stage-007', name: 'Sync to Search', order: 3, type: 'load' },
    ],
  },
};

export const demoPipelineRuns: PipelineRunSummary[] = [
  { id: 'run-001', pipeline_id: 'pipeline-001', pipeline_name: 'Customer Data Sync', run_number: 156, status: 'completed', started_at: '2026-01-19T02:00:00Z', completed_at: '2026-01-19T02:45:00Z', duration_seconds: 2700, triggered_by: 'schedule' },
  { id: 'run-002', pipeline_id: 'pipeline-002', pipeline_name: 'Product Catalog Update', run_number: 3842, status: 'completed', started_at: '2026-01-19T14:00:00Z', completed_at: '2026-01-19T14:12:00Z', duration_seconds: 720, triggered_by: 'schedule' },
  { id: 'run-003', pipeline_id: 'pipeline-003', pipeline_name: 'Analytics ETL', run_number: 89, status: 'failed', started_at: '2026-01-18T04:00:00Z', completed_at: '2026-01-18T04:32:00Z', duration_seconds: 1920, triggered_by: 'schedule' },
  { id: 'run-004', pipeline_id: 'pipeline-001', pipeline_name: 'Customer Data Sync', run_number: 155, status: 'completed', started_at: '2026-01-18T02:00:00Z', completed_at: '2026-01-18T02:42:00Z', duration_seconds: 2520, triggered_by: 'schedule' },
  { id: 'run-005', pipeline_id: 'pipeline-004', pipeline_name: 'ML Model Refresh', run_number: 12, status: 'running', started_at: '2026-01-19T14:30:00Z', completed_at: null, duration_seconds: null, triggered_by: 'manual' },
];

// =============================================================================
// Settings - System
// =============================================================================

export const demoSystemSettings: SystemSettings = {
  instance_name: 'Open Forge Demo',
  instance_url: 'https://demo.openforge.io',
  admin_email: 'admin@openforge.io',
  session_timeout_minutes: 60,
  require_mfa: true,
  allow_self_registration: false,
  default_user_role: 'viewer',
};

// =============================================================================
// Settings - Connectors
// =============================================================================

export const demoConnectors: ConnectorSummary[] = [
  { id: 'conn-001', name: 'Production PostgreSQL', type: 'database', provider: 'PostgreSQL', status: 'active', last_tested: '2026-01-19T14:00:00Z', last_test_success: true },
  { id: 'conn-002', name: 'Salesforce CRM', type: 'api', provider: 'Salesforce', status: 'active', last_tested: '2026-01-19T13:30:00Z', last_test_success: true },
  { id: 'conn-003', name: 'AWS S3 Data Lake', type: 'file_storage', provider: 'AWS S3', status: 'active', last_tested: '2026-01-19T12:00:00Z', last_test_success: true },
  { id: 'conn-004', name: 'Kafka Event Stream', type: 'message_queue', provider: 'Apache Kafka', status: 'active', last_tested: '2026-01-19T14:15:00Z', last_test_success: true },
  { id: 'conn-005', name: 'Snowflake Warehouse', type: 'database', provider: 'Snowflake', status: 'error', last_tested: '2026-01-19T10:00:00Z', last_test_success: false },
  { id: 'conn-006', name: 'Azure Blob Storage', type: 'cloud_service', provider: 'Azure', status: 'inactive', last_tested: null, last_test_success: null },
];

// =============================================================================
// Settings - Users
// =============================================================================

export const demoUsers: UserSummary[] = [
  { id: 'user-001', name: 'John Admin', email: 'john.admin@company.com', role: 'admin', status: 'active', last_login: '2026-01-19T14:30:00Z', mfa_enabled: true, created_at: '2025-01-15T10:00:00Z' },
  { id: 'user-002', name: 'Sarah Editor', email: 'sarah.editor@company.com', role: 'editor', status: 'active', last_login: '2026-01-19T11:00:00Z', mfa_enabled: true, created_at: '2025-03-20T09:00:00Z' },
  { id: 'user-003', name: 'Mike Viewer', email: 'mike.viewer@company.com', role: 'viewer', status: 'active', last_login: '2026-01-18T16:00:00Z', mfa_enabled: false, created_at: '2025-06-10T14:00:00Z' },
  { id: 'user-004', name: 'API Service Account', email: 'api@company.com', role: 'api', status: 'active', last_login: '2026-01-19T14:35:00Z', mfa_enabled: false, created_at: '2025-02-01T08:00:00Z' },
  { id: 'user-005', name: 'Jane Pending', email: 'jane.pending@company.com', role: 'viewer', status: 'pending', last_login: null, mfa_enabled: false, created_at: '2026-01-19T12:00:00Z' },
];

// =============================================================================
// Settings - Audit Logs
// =============================================================================

export const demoAuditLogs: AuditLogEntry[] = [
  { id: 'audit-001', timestamp: '2026-01-19T14:35:00Z', action: 'user.login', category: 'auth', actor: 'john.admin@company.com', actor_type: 'user', resource_type: 'session', resource_id: 'sess-123', details: { method: 'password', mfa: true }, ip_address: '192.168.1.100' },
  { id: 'audit-002', timestamp: '2026-01-19T14:30:00Z', action: 'engagement.update', category: 'data', actor: 'sarah.editor@company.com', actor_type: 'user', resource_type: 'engagement', resource_id: 'eng-001', details: { field: 'status', old: 'pending', new: 'in_progress' }, ip_address: '192.168.1.101' },
  { id: 'audit-003', timestamp: '2026-01-19T14:15:00Z', action: 'pipeline.trigger', category: 'pipeline', actor: 'Data Integration Agent', actor_type: 'agent', resource_type: 'pipeline', resource_id: 'pipeline-001', details: { trigger: 'schedule' }, ip_address: null },
  { id: 'audit-004', timestamp: '2026-01-19T14:00:00Z', action: 'settings.update', category: 'config', actor: 'john.admin@company.com', actor_type: 'user', resource_type: 'system_settings', resource_id: 'settings', details: { field: 'session_timeout_minutes', old: 30, new: 60 }, ip_address: '192.168.1.100' },
  { id: 'audit-005', timestamp: '2026-01-19T13:45:00Z', action: 'agent.task.complete', category: 'agent', actor: 'Discovery Agent', actor_type: 'agent', resource_type: 'task', resource_id: 'task-002', details: { iterations: 8, status: 'completed' }, ip_address: null },
  { id: 'audit-006', timestamp: '2026-01-19T13:30:00Z', action: 'user.create', category: 'user', actor: 'john.admin@company.com', actor_type: 'user', resource_type: 'user', resource_id: 'user-005', details: { email: 'jane.pending@company.com', role: 'viewer' }, ip_address: '192.168.1.100' },
];

// =============================================================================
// Reviews
// =============================================================================

export const demoReviews: ReviewItemSummary[] = [
  { id: 'review-001', title: 'Schema mapping validation for Customer entity', category: 'mapping', priority: 2, status: 'queued', created_at: '2026-01-19T14:00:00Z', assigned_to: null },
  { id: 'review-002', title: 'Data quality check - missing values in OrderDate', category: 'data_quality', priority: 1, status: 'in_review', created_at: '2026-01-19T13:30:00Z', assigned_to: 'sarah.editor@company.com' },
  { id: 'review-003', title: 'Agent output review - entity extraction results', category: 'agent_output', priority: 3, status: 'queued', created_at: '2026-01-19T12:00:00Z', assigned_to: null },
  { id: 'review-004', title: 'Configuration change - pipeline schedule update', category: 'configuration', priority: 4, status: 'completed', created_at: '2026-01-18T16:00:00Z', assigned_to: 'john.admin@company.com' },
  { id: 'review-005', title: 'Data quality alert - duplicate records detected', category: 'data_quality', priority: 1, status: 'deferred', created_at: '2026-01-18T10:00:00Z', assigned_to: 'sarah.editor@company.com' },
];

export const demoReviewDetails: Record<string, ReviewItem> = {
  'review-001': {
    id: 'review-001',
    title: 'Schema mapping validation for Customer entity',
    category: 'mapping',
    priority: 2,
    status: 'queued',
    created_at: '2026-01-19T14:00:00Z',
    assigned_to: null,
    description: 'The schema mapping agent has proposed field mappings for the Customer entity. Please review and validate the suggested mappings before they are applied to the target schema.',
    context_data: { source_table: 'raw_customers', target_entity: 'Customer', proposed_mappings: 12, confidence_score: 0.87 },
    engagement_id: 'eng-001',
    created_by: 'Schema Mapping Agent',
  },
  'review-002': {
    id: 'review-002',
    title: 'Data quality check - missing values in OrderDate',
    category: 'data_quality',
    priority: 1,
    status: 'in_review',
    created_at: '2026-01-19T13:30:00Z',
    assigned_to: 'sarah.editor@company.com',
    description: 'Data quality validation detected 3.2% of records with missing OrderDate values. This exceeds the configured threshold of 1%. Please review and decide on remediation.',
    context_data: { total_records: 125000, missing_count: 4000, threshold: 0.01, actual_rate: 0.032 },
    engagement_id: 'eng-001',
    created_by: 'Data Quality Agent',
  },
  'review-003': {
    id: 'review-003',
    title: 'Agent output review - entity extraction results',
    category: 'agent_output',
    priority: 3,
    status: 'queued',
    created_at: '2026-01-19T12:00:00Z',
    assigned_to: null,
    description: 'The discovery agent has identified potential entities from the source data. Review the extracted entities and relationships before adding them to the ontology.',
    context_data: { entities_found: 8, relationships_found: 12, source: 'supply_chain_data' },
    engagement_id: 'eng-002',
    created_by: 'Discovery Agent',
  },
};

export const demoReviewStats: ReviewStats = {
  queued: 2,
  in_review: 1,
  completed_today: 5,
  avg_review_time_minutes: 12,
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
