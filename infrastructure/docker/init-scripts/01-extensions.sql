-- Open Forge Database Initialization
-- Extensions and base schema setup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "age";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Load Apache AGE
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create the knowledge graph
SELECT create_graph('openforge_graph');

-- Schema for core entities
CREATE SCHEMA IF NOT EXISTS openforge;

-- Engagement states table
CREATE TABLE openforge.engagements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'discovery',
    phase VARCHAR(50) NOT NULL DEFAULT 'initial',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Agent task tracking
CREATE TABLE openforge.agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id UUID REFERENCES openforge.engagements(id),
    agent_type VARCHAR(100) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Data source registry
CREATE TABLE openforge.data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id UUID REFERENCES openforge.engagements(id),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    connection_config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ontology definitions
CREATE TABLE openforge.ontology_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id UUID REFERENCES openforge.engagements(id),
    name VARCHAR(255) NOT NULL,
    schema_definition JSONB NOT NULL,
    linkml_yaml TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(engagement_id, name, version)
);

-- Approval workflows
CREATE TABLE openforge.approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id UUID REFERENCES openforge.engagements(id),
    task_id UUID REFERENCES openforge.agent_tasks(id),
    approval_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    requester_agent VARCHAR(100) NOT NULL,
    request_data JSONB NOT NULL,
    response_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    responded_at TIMESTAMPTZ
);

-- Embeddings storage for semantic search
CREATE TABLE openforge.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_type, source_id, content_hash)
);

-- Create vector similarity index
CREATE INDEX embeddings_vector_idx ON openforge.embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create text search indexes
CREATE INDEX engagements_name_trgm_idx ON openforge.engagements
USING gin (name gin_trgm_ops);

CREATE INDEX data_sources_name_trgm_idx ON openforge.data_sources
USING gin (name gin_trgm_ops);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION openforge.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER engagements_updated_at
    BEFORE UPDATE ON openforge.engagements
    FOR EACH ROW EXECUTE FUNCTION openforge.update_updated_at();

CREATE TRIGGER data_sources_updated_at
    BEFORE UPDATE ON openforge.data_sources
    FOR EACH ROW EXECUTE FUNCTION openforge.update_updated_at();

CREATE TRIGGER ontology_types_updated_at
    BEFORE UPDATE ON openforge.ontology_types
    FOR EACH ROW EXECUTE FUNCTION openforge.update_updated_at();

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA openforge TO foundry;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA openforge TO foundry;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA openforge TO foundry;
