"""
Open Forge MCP Server Module.

Exposes Open Forge capabilities as MCP tools:
- query_ontology: Query the ontology for entities, relationships, and schemas
- trigger_pipeline: Trigger data pipelines with configuration overrides
- generate_code: Generate code from ontology schemas

Example usage:
    # Run as standalone server
    python -m mcp_server.open_forge_mcp

    # Or import and use programmatically
    from mcp_server import OpenForgeMCPServer
    server = OpenForgeMCPServer()
    await server.run()
"""

from mcp_server.open_forge_mcp import (
    OpenForgeMCPServer,
    query_ontology,
    trigger_pipeline,
    generate_code,
)

__version__ = "0.1.0"

__all__ = [
    "OpenForgeMCPServer",
    "query_ontology",
    "trigger_pipeline",
    "generate_code",
]
