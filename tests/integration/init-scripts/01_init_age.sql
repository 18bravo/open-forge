-- Initialize Apache AGE extension for graph database testing
-- This script runs on PostgreSQL container startup

-- Create the AGE extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS age;

-- Add age to the search path
ALTER DATABASE openforge_test SET search_path = ag_catalog, "$user", public;

-- Create a default test graph
SELECT create_graph('test_graph');

-- Grant permissions for the test user
GRANT USAGE ON SCHEMA ag_catalog TO foundry;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ag_catalog TO foundry;
