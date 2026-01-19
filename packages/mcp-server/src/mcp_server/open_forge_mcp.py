"""
Open Forge MCP Server.

Exposes Open Forge capabilities as MCP tools for use by AI agents
and other MCP-compatible clients.

Tools provided:
- query_ontology: Query ontology schemas, entities, and relationships
- trigger_pipeline: Trigger data processing pipelines
- generate_code: Generate code from ontology schemas

Usage:
    # Run directly
    python -m mcp_server.open_forge_mcp

    # Or use the CLI entry point
    open-forge-mcp
"""
import asyncio
import json
import os
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field


# Server instance
server = Server("open-forge")


class OntologyQueryResult(BaseModel):
    """Result from an ontology query."""

    engagement_id: str
    object_type: str
    items: list[dict[str, Any]]
    total_count: int
    filters_applied: dict[str, Any]


class PipelineResult(BaseModel):
    """Result from triggering a pipeline."""

    engagement_id: str
    pipeline_id: str
    run_id: str
    status: str
    message: str


class CodeGenerationResult(BaseModel):
    """Result from code generation."""

    engagement_id: str
    generator_type: str
    files_generated: list[str]
    output_directory: str
    success: bool
    message: str


class OpenForgeClient:
    """
    Client for interacting with Open Forge services.

    This client handles communication with the Open Forge API
    for ontology queries, pipeline triggers, and code generation.
    """

    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the Open Forge client.

        Args:
            api_url: Base URL for Open Forge API. Defaults to environment variable
                     or localhost.
        """
        self.api_url = api_url or os.environ.get(
            "OPEN_FORGE_API_URL", "http://localhost:8000"
        )

    async def query_ontology(
        self,
        engagement_id: str,
        object_type: str,
        filters: Optional[dict[str, Any]] = None,
    ) -> OntologyQueryResult:
        """
        Query the ontology for entities of a specific type.

        Args:
            engagement_id: ID of the engagement to query
            object_type: Type of ontology object (entity, relationship, property, schema)
            filters: Optional filters to apply

        Returns:
            Query result with matching items
        """
        # In production, this would make an HTTP call to the Open Forge API
        # For now, we return a mock result structure
        filters = filters or {}

        # Simulated response - in production this calls the actual ontology service
        return OntologyQueryResult(
            engagement_id=engagement_id,
            object_type=object_type,
            items=[],
            total_count=0,
            filters_applied=filters,
        )

    async def trigger_pipeline(
        self,
        engagement_id: str,
        pipeline_id: str,
        config_overrides: Optional[dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Trigger a data processing pipeline.

        Args:
            engagement_id: ID of the engagement
            pipeline_id: ID of the pipeline to trigger
            config_overrides: Optional configuration overrides

        Returns:
            Pipeline trigger result
        """
        config_overrides = config_overrides or {}

        # Simulated response - in production this calls Dagster or the pipeline orchestrator
        return PipelineResult(
            engagement_id=engagement_id,
            pipeline_id=pipeline_id,
            run_id=f"run_{engagement_id}_{pipeline_id}_{asyncio.get_event_loop().time()}",
            status="triggered",
            message=f"Pipeline {pipeline_id} triggered successfully",
        )

    async def generate_code(
        self,
        engagement_id: str,
        generator_type: str,
        target_entities: Optional[list[str]] = None,
    ) -> CodeGenerationResult:
        """
        Generate code from ontology schemas.

        Args:
            engagement_id: ID of the engagement
            generator_type: Type of code generator (fastapi, orm, typescript, graphql, tests)
            target_entities: Optional list of entity names to generate for

        Returns:
            Code generation result
        """
        target_entities = target_entities or []

        # Simulated response - in production this calls the codegen service
        return CodeGenerationResult(
            engagement_id=engagement_id,
            generator_type=generator_type,
            files_generated=[],
            output_directory=f"/generated/{engagement_id}/{generator_type}",
            success=True,
            message=f"Code generation initiated for {generator_type}",
        )


# Global client instance
_client: Optional[OpenForgeClient] = None


def get_client() -> OpenForgeClient:
    """Get or create the Open Forge client."""
    global _client
    if _client is None:
        _client = OpenForgeClient()
    return _client


@server.tool()
async def query_ontology(
    engagement_id: str,
    object_type: str,
    filters: Optional[dict[str, Any]] = None,
) -> str:
    """
    Query the Open Forge ontology for entities, relationships, and schemas.

    Args:
        engagement_id: The unique identifier for the engagement/project
        object_type: Type of ontology object to query. Options:
            - "entity": Query entity definitions
            - "relationship": Query relationship definitions
            - "property": Query property definitions
            - "schema": Query full schema definitions
        filters: Optional dictionary of filters to apply:
            - name: Filter by name (exact or partial match)
            - namespace: Filter by namespace
            - created_after: Filter by creation date
            - tags: Filter by tags (list)

    Returns:
        JSON string containing query results with:
        - items: List of matching ontology objects
        - total_count: Total number of matches
        - filters_applied: Filters that were applied

    Example:
        query_ontology("eng-123", "entity", {"namespace": "customer"})
    """
    client = get_client()
    result = await client.query_ontology(
        engagement_id=engagement_id,
        object_type=object_type,
        filters=filters,
    )
    return result.model_dump_json(indent=2)


@server.tool()
async def trigger_pipeline(
    engagement_id: str,
    pipeline_id: str,
    config_overrides: Optional[dict[str, Any]] = None,
) -> str:
    """
    Trigger a data processing pipeline in Open Forge.

    Args:
        engagement_id: The unique identifier for the engagement/project
        pipeline_id: The identifier of the pipeline to trigger. Common pipelines:
            - "ingestion": Data ingestion from sources
            - "transformation": Data transformation and cleansing
            - "ontology_compilation": Compile ontology schemas
            - "code_generation": Generate code from schemas
        config_overrides: Optional configuration overrides:
            - source_config: Override source connection settings
            - target_config: Override target settings
            - partition_key: Specify partition for processing
            - run_mode: "full" or "incremental"

    Returns:
        JSON string containing:
        - run_id: Unique identifier for this pipeline run
        - status: Current status (triggered, running, completed, failed)
        - message: Human-readable status message

    Example:
        trigger_pipeline("eng-123", "ingestion", {"run_mode": "incremental"})
    """
    client = get_client()
    result = await client.trigger_pipeline(
        engagement_id=engagement_id,
        pipeline_id=pipeline_id,
        config_overrides=config_overrides,
    )
    return result.model_dump_json(indent=2)


@server.tool()
async def generate_code(
    engagement_id: str,
    generator_type: str,
    target_entities: Optional[list[str]] = None,
) -> str:
    """
    Generate code from Open Forge ontology schemas.

    Args:
        engagement_id: The unique identifier for the engagement/project
        generator_type: Type of code to generate:
            - "fastapi": Generate FastAPI route handlers
            - "orm": Generate SQLAlchemy ORM models
            - "typescript": Generate TypeScript interfaces
            - "graphql": Generate GraphQL schema and resolvers
            - "tests": Generate pytest test files
            - "hooks": Generate React Query hooks
        target_entities: Optional list of entity names to generate code for.
            If not specified, generates for all entities in the ontology.

    Returns:
        JSON string containing:
        - files_generated: List of generated file paths
        - output_directory: Directory where files were written
        - success: Boolean indicating success
        - message: Human-readable result message

    Example:
        generate_code("eng-123", "fastapi", ["Customer", "Order", "Product"])
    """
    client = get_client()
    result = await client.generate_code(
        engagement_id=engagement_id,
        generator_type=generator_type,
        target_entities=target_entities,
    )
    return result.model_dump_json(indent=2)


class OpenForgeMCPServer:
    """
    Open Forge MCP Server wrapper class.

    Provides a high-level interface for running the MCP server
    with proper lifecycle management.
    """

    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the server.

        Args:
            api_url: Optional Open Forge API URL
        """
        global _client
        _client = OpenForgeClient(api_url=api_url)
        self.server = server

    async def run(self):
        """Run the MCP server."""
        await self.server.run()

    def get_tools(self) -> list[str]:
        """Get list of available tool names."""
        return ["query_ontology", "trigger_pipeline", "generate_code"]


def main():
    """Entry point for running the MCP server."""
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
