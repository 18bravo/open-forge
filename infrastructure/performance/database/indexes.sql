-- =============================================================================
-- Open Forge Database Indexes
-- Recommended indexes for optimal query performance
-- =============================================================================

-- Run this script with: psql -d openforge -f indexes.sql

-- =============================================================================
-- ENGAGEMENT INDEXES
-- =============================================================================

-- Primary lookup by ID (already exists via PK, but explicit for clarity)
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_engagements_id ON engagements(id);

-- Filter by status (common filter)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_status
    ON engagements(status)
    WHERE status IS NOT NULL;

-- Filter by organization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_organization_id
    ON engagements(organization_id);

-- Combined org + status for common query pattern
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_org_status
    ON engagements(organization_id, status);

-- Date range queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_created_at
    ON engagements(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_updated_at
    ON engagements(updated_at DESC);

-- Full-text search on name and description
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_name_search
    ON engagements USING gin(to_tsvector('english', name));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_description_search
    ON engagements USING gin(to_tsvector('english', COALESCE(description, '')));

-- JSONB metadata queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagements_metadata
    ON engagements USING gin(metadata jsonb_path_ops);

-- =============================================================================
-- AGENT TASK INDEXES
-- =============================================================================

-- Foreign key to engagement
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_engagement_id
    ON agent_tasks(engagement_id);

-- Status filtering (common query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_status
    ON agent_tasks(status);

-- Priority for queue ordering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_priority_created
    ON agent_tasks(priority DESC, created_at ASC)
    WHERE status IN ('pending', 'queued');

-- Combined engagement + status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_engagement_status
    ON agent_tasks(engagement_id, status);

-- Task type filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_type
    ON agent_tasks(task_type);

-- Date range for completed tasks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_completed_at
    ON agent_tasks(completed_at DESC)
    WHERE completed_at IS NOT NULL;

-- Agent assignment
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_assigned_agent
    ON agent_tasks(assigned_agent_id)
    WHERE assigned_agent_id IS NOT NULL;

-- Partial index for active tasks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_active
    ON agent_tasks(created_at DESC)
    WHERE status NOT IN ('completed', 'failed', 'cancelled');

-- =============================================================================
-- DATA SOURCE INDEXES
-- =============================================================================

-- Organization lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_sources_organization_id
    ON data_sources(organization_id);

-- Type filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_sources_type
    ON data_sources(source_type);

-- Active data sources
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_sources_active
    ON data_sources(organization_id)
    WHERE is_active = true;

-- Connection status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_sources_connection_status
    ON data_sources(connection_status);

-- Last sync time for scheduling
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_sources_last_sync
    ON data_sources(last_sync_at)
    WHERE is_active = true;

-- =============================================================================
-- AUDIT LOG INDEXES
-- =============================================================================

-- User activity lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_id
    ON audit_logs(user_id);

-- Entity type + ID for specific entity history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_entity
    ON audit_logs(entity_type, entity_id);

-- Action filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_action
    ON audit_logs(action);

-- Time-based queries (most important for audit logs)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_at
    ON audit_logs(created_at DESC);

-- Combined user + time for user activity history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_time
    ON audit_logs(user_id, created_at DESC);

-- Organization audit trail
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_organization_id
    ON audit_logs(organization_id, created_at DESC);

-- IP address tracking (for security analysis)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_ip_address
    ON audit_logs(ip_address)
    WHERE ip_address IS NOT NULL;

-- =============================================================================
-- USER INDEXES
-- =============================================================================

-- Email lookup (unique, case-insensitive)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower
    ON users(lower(email));

-- Organization membership
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_organization_id
    ON users(organization_id);

-- Active users
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active
    ON users(organization_id)
    WHERE is_active = true;

-- Last login tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login
    ON users(last_login_at DESC)
    WHERE last_login_at IS NOT NULL;

-- =============================================================================
-- VECTOR EMBEDDING INDEXES (pgvector)
-- =============================================================================

-- HNSW index for vector similarity search (fastest for high-dimensional vectors)
-- Parameters:
--   m: Maximum number of connections per layer (default 16)
--   ef_construction: Size of dynamic candidate list for construction (default 64)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_hnsw
    ON embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (good for smaller datasets)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_ivfflat
--     ON embeddings USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);

-- Source document reference
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_source
    ON embeddings(source_type, source_id);

-- Engagement embeddings
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_engagement_id
    ON embeddings(engagement_id)
    WHERE engagement_id IS NOT NULL;

-- Chunk position for retrieval
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_chunk_position
    ON embeddings(source_id, chunk_index);

-- =============================================================================
-- PIPELINE RUN INDEXES (Dagster-related)
-- =============================================================================

-- Pipeline run status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_runs_status
    ON pipeline_runs(status);

-- Pipeline name + status for filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_runs_name_status
    ON pipeline_runs(pipeline_name, status);

-- Engagement association
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_runs_engagement_id
    ON pipeline_runs(engagement_id)
    WHERE engagement_id IS NOT NULL;

-- Time-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_runs_started_at
    ON pipeline_runs(started_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_runs_completed_at
    ON pipeline_runs(completed_at DESC)
    WHERE completed_at IS NOT NULL;

-- Active runs
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pipeline_runs_active
    ON pipeline_runs(started_at DESC)
    WHERE status IN ('running', 'pending', 'queued');

-- =============================================================================
-- SESSION/TOKEN INDEXES
-- =============================================================================

-- Token lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token
    ON sessions(token)
    WHERE expires_at > NOW();

-- User sessions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_id
    ON sessions(user_id);

-- Expired session cleanup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires_at
    ON sessions(expires_at)
    WHERE expires_at < NOW();

-- =============================================================================
-- ORGANIZATION INDEXES
-- =============================================================================

-- Slug lookup (for URLs)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_slug
    ON organizations(slug);

-- Active organizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_active
    ON organizations(created_at DESC)
    WHERE is_active = true;

-- =============================================================================
-- COMPOSITE INDEXES FOR COMMON QUERIES
-- =============================================================================

-- Dashboard query: Recent engagements with status for an org
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_engagements
    ON engagements(organization_id, status, updated_at DESC);

-- Task queue: Next task to process
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_queue_next
    ON agent_tasks(priority DESC, created_at ASC)
    WHERE status = 'pending'
    AND assigned_agent_id IS NULL;

-- Search results: Combined FTS and metadata
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_engagement_search_combined
    ON engagements USING gin(
        to_tsvector('english', name || ' ' || COALESCE(description, ''))
    );

-- =============================================================================
-- INDEX MAINTENANCE QUERIES
-- =============================================================================

-- View index usage statistics
-- SELECT
--     schemaname,
--     relname,
--     indexrelname,
--     idx_scan,
--     idx_tup_read,
--     idx_tup_fetch,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan DESC;

-- Find unused indexes (candidates for removal)
-- SELECT
--     schemaname,
--     relname,
--     indexrelname,
--     idx_scan,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size
-- FROM pg_stat_user_indexes
-- WHERE idx_scan = 0
-- AND indexrelname NOT LIKE '%_pkey'
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- Reindex bloated indexes (run during maintenance window)
-- REINDEX INDEX CONCURRENTLY idx_name;

-- =============================================================================
-- ANALYZE TABLES AFTER INDEX CREATION
-- =============================================================================

ANALYZE engagements;
ANALYZE agent_tasks;
ANALYZE data_sources;
ANALYZE audit_logs;
ANALYZE users;
ANALYZE embeddings;
ANALYZE pipeline_runs;
ANALYZE sessions;
ANALYZE organizations;

-- =============================================================================
-- SET INDEX PARAMETERS FOR VECTOR SEARCH
-- =============================================================================

-- Set HNSW search parameters (can be set per-session)
-- SET hnsw.ef_search = 100;  -- Higher = more accurate, slower

-- For IVFFlat indexes
-- SET ivfflat.probes = 10;  -- Higher = more accurate, slower
