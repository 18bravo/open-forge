-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Load AGE
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create default graph
SELECT create_graph('ontology_graph');

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ontology_meta;
CREATE SCHEMA IF NOT EXISTS objects;
CREATE SCHEMA IF NOT EXISTS lineage;
CREATE SCHEMA IF NOT EXISTS engagements;

-- Ontology metadata tables
CREATE TABLE ontology_meta.object_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    schema_yaml TEXT NOT NULL,
    compiled_at TIMESTAMP DEFAULT NOW(),
    version VARCHAR(50),
    checksum VARCHAR(64)
);

CREATE TABLE ontology_meta.relationship_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type_id UUID REFERENCES ontology_meta.object_types(id),
    target_type_id UUID REFERENCES ontology_meta.object_types(id),
    cardinality VARCHAR(10),
    has_edge_properties BOOLEAN DEFAULT FALSE,
    edge_properties_schema JSONB,
    UNIQUE(name, source_type_id, target_type_id)
);

CREATE TABLE ontology_meta.ontology_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id VARCHAR(255),
    version VARCHAR(50) NOT NULL,
    schema_yaml TEXT NOT NULL,
    compiled_artifacts JSONB,
    deployed_at TIMESTAMP DEFAULT NOW(),
    deployed_by VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE
);

-- Engagement tracking tables
CREATE TABLE engagements.engagements (
    id VARCHAR(255) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE engagements.checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id VARCHAR(255) REFERENCES engagements.engagements(id),
    thread_id VARCHAR(255),
    checkpoint_ns VARCHAR(255),
    checkpoint JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_checkpoints_engagement ON engagements.checkpoints(engagement_id);
CREATE INDEX idx_checkpoints_thread ON engagements.checkpoints(thread_id);

-- Lineage tracking
CREATE TABLE lineage.data_flow (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_asset VARCHAR(255),
    target_asset VARCHAR(255),
    execution_id UUID,
    executed_at TIMESTAMP DEFAULT NOW(),
    record_count INT,
    status VARCHAR(50),
    error_message TEXT
);

CREATE TABLE lineage.object_provenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_type VARCHAR(255),
    object_id VARCHAR(255),
    source_system VARCHAR(100),
    source_table VARCHAR(255),
    source_record_id VARCHAR(255),
    transformation_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_data_flow_source ON lineage.data_flow(source_asset);
CREATE INDEX idx_data_flow_target ON lineage.data_flow(target_asset);
CREATE INDEX idx_provenance_type ON lineage.object_provenance(object_type);
CREATE INDEX idx_provenance_source ON lineage.object_provenance(source_system);