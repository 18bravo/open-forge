"""
Context builder for ontology-aware LLM requests.

This module provides the ContextBuilder which injects ontology schema,
RAG results, and tool definitions into LLM requests.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

from forge_ai.providers.base import CompletionRequest, Message, ToolDefinition

logger = structlog.get_logger(__name__)


@dataclass
class ContextConfig:
    """Configuration for context injection."""

    ontology_id: str

    # Schema injection
    include_schema: bool = True
    schema_format: str = "concise"  # 'concise', 'full', 'json'

    # RAG configuration
    rag_query: str | None = None
    rag_object_types: list[str] | None = None
    rag_top_k: int = 5

    # Tool configuration
    enable_tools: bool = True
    tool_types: list[str] = field(
        default_factory=lambda: ["get_object", "search_objects", "traverse_links"]
    )

    # Context limits
    max_schema_tokens: int = 2000
    max_rag_tokens: int = 3000


@dataclass
class OntologyContext:
    """The built context for an LLM request."""

    schema_context: str | None = None
    rag_context: str | None = None
    tools: list[ToolDefinition] = field(default_factory=list)

    # Metadata
    ontology_id: str = ""
    object_types_included: list[str] = field(default_factory=list)
    rag_results_count: int = 0


class ContextBuilder:
    """
    Builds ontology-aware context for LLM requests.

    Handles:
    - Schema injection (object types, properties, relationships)
    - RAG retrieval and formatting
    - Tool definition generation
    """

    def __init__(
        self,
        ontology_client: Any | None = None,  # OntologyClient
        rag_retriever: Any | None = None,  # RAGRetriever
    ):
        """
        Initialize the context builder.

        Args:
            ontology_client: Client for ontology queries.
            rag_retriever: RAG retriever for semantic search.
        """
        self.ontology_client = ontology_client
        self.rag_retriever = rag_retriever

    async def build(self, config: ContextConfig) -> OntologyContext:
        """
        Build the context based on configuration.

        Args:
            config: Context configuration.

        Returns:
            OntologyContext with schema, RAG, and tools.
        """
        context = OntologyContext(ontology_id=config.ontology_id)

        # Build schema context
        if config.include_schema:
            context.schema_context = await self._build_schema_context(config)

        # Build RAG context
        if config.rag_query:
            context.rag_context, context.rag_results_count = await self._build_rag_context(
                config
            )

        # Build tools
        if config.enable_tools:
            context.tools = self._build_tools(config)

        return context

    async def inject(
        self,
        request: CompletionRequest,
        config: ContextConfig,
    ) -> CompletionRequest:
        """
        Inject ontology context into a completion request.

        Args:
            request: The original completion request.
            config: Context configuration.

        Returns:
            Modified request with context injected.
        """
        context = await self.build(config)

        # Build system message parts
        system_parts = []

        if context.schema_context:
            system_parts.append(context.schema_context)

        if context.rag_context:
            system_parts.append(context.rag_context)

        # Prepend to messages
        if system_parts:
            context_message = Message(
                role="system",
                content="\n\n".join(system_parts),
            )

            # Insert context at the beginning
            new_messages = [context_message] + list(request.messages)
            request = request.model_copy()
            request.messages = new_messages

        # Add tools
        if context.tools:
            existing_tools = request.tools or []
            request.tools = existing_tools + context.tools

        return request

    async def _build_schema_context(self, config: ContextConfig) -> str:
        """Build schema context for the ontology."""
        if self.ontology_client is None:
            logger.warning("Ontology client not configured, skipping schema context")
            return ""

        try:
            schema = await self.ontology_client.get_schema(config.ontology_id)

            if config.schema_format == "concise":
                return self._format_schema_concise(schema)
            elif config.schema_format == "json":
                return self._format_schema_json(schema)
            else:
                return self._format_schema_full(schema)

        except Exception as e:
            logger.warning("Failed to build schema context", error=str(e))
            return ""

    async def _build_rag_context(
        self, config: ContextConfig
    ) -> tuple[str, int]:
        """Build RAG context from retrieved documents."""
        if self.rag_retriever is None or not config.rag_query:
            return "", 0

        try:
            results = await self.rag_retriever.retrieve(
                query=config.rag_query,
                ontology_id=config.ontology_id,
                object_types=config.rag_object_types,
                top_k=config.rag_top_k,
            )

            if not results:
                return "", 0

            # Format results
            formatted_parts = ["## Relevant Information\n"]
            for i, result in enumerate(results, 1):
                formatted_parts.append(
                    f"### Result {i} (relevance: {result.score:.2f})\n"
                    f"Type: {result.object_type or 'unknown'}\n"
                    f"{result.content}\n"
                )

            return "\n".join(formatted_parts), len(results)

        except Exception as e:
            logger.warning("Failed to build RAG context", error=str(e))
            return "", 0

    def _build_tools(self, config: ContextConfig) -> list[ToolDefinition]:
        """Build tool definitions for ontology operations."""
        tools = []

        if "get_object" in config.tool_types:
            tools.append(
                ToolDefinition(
                    name="get_object",
                    description="Retrieve a specific object by type and ID from the ontology",
                    parameters={
                        "type": "object",
                        "properties": {
                            "object_type": {
                                "type": "string",
                                "description": "The type of object to retrieve",
                            },
                            "object_id": {
                                "type": "string",
                                "description": "The ID of the object to retrieve",
                            },
                        },
                        "required": ["object_type", "object_id"],
                    },
                )
            )

        if "search_objects" in config.tool_types:
            tools.append(
                ToolDefinition(
                    name="search_objects",
                    description="Search for objects matching criteria in the ontology",
                    parameters={
                        "type": "object",
                        "properties": {
                            "object_type": {
                                "type": "string",
                                "description": "The type of objects to search",
                            },
                            "filters": {
                                "type": "object",
                                "description": "Filter criteria as key-value pairs",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10,
                            },
                        },
                        "required": ["object_type"],
                    },
                )
            )

        if "traverse_links" in config.tool_types:
            tools.append(
                ToolDefinition(
                    name="traverse_links",
                    description="Follow links from an object to related objects",
                    parameters={
                        "type": "object",
                        "properties": {
                            "object_type": {
                                "type": "string",
                                "description": "The type of the source object",
                            },
                            "object_id": {
                                "type": "string",
                                "description": "The ID of the source object",
                            },
                            "link_type": {
                                "type": "string",
                                "description": "The type of link to follow",
                            },
                        },
                        "required": ["object_type", "object_id", "link_type"],
                    },
                )
            )

        return tools

    def _format_schema_concise(self, schema: Any) -> str:
        """Format schema in concise format."""
        # Stub implementation - would format actual schema
        return "## Data Schema\n\n[Schema information would be inserted here]"

    def _format_schema_json(self, schema: Any) -> str:
        """Format schema as JSON."""
        import json

        if hasattr(schema, "model_dump"):
            return f"## Data Schema (JSON)\n\n```json\n{json.dumps(schema.model_dump(), indent=2)}\n```"
        return "## Data Schema (JSON)\n\n[Schema information would be inserted here]"

    def _format_schema_full(self, schema: Any) -> str:
        """Format schema with full details."""
        return "## Data Schema (Full)\n\n[Full schema information would be inserted here]"
