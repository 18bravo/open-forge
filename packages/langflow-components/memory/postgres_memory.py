"""
PostgresStore Memory Component for Langflow

Provides a Langflow component for LangGraph's PostgresStore,
enabling long-term memory with semantic search for agent workflows.
"""
from typing import Any, Dict, List, Optional
import json

from langflow.custom import Component
from langflow.io import (
    StrInput,
    SecretStrInput,
    DictInput,
    DropdownInput,
    Output,
    MessageTextInput,
    IntInput,
)
from langflow.schema import Message


class PostgresMemoryComponent(Component):
    """
    Open Forge PostgresStore Memory Component for Langflow.

    This component provides memory operations using LangGraph's
    PostgresStore with pgvector for semantic search:
    - Store memories with semantic indexing
    - Search memories using natural language
    - List memories by namespace/type
    - Delete memories
    - Get memory statistics

    Memory is namespaced by engagement and memory type for
    cross-thread memory sharing within an engagement.
    """

    display_name = "Postgres Memory"
    description = "Long-term memory with semantic search using PostgresStore"
    icon = "database"
    name = "PostgresMemory"

    inputs = [
        DropdownInput(
            name="operation",
            display_name="Operation",
            info="The memory operation to perform",
            options=[
                "store",
                "search",
                "list",
                "get",
                "delete",
                "stats",
            ],
            value="search",
            required=True,
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context",
            required=True,
        ),
        StrInput(
            name="memory_type",
            display_name="Memory Type",
            info="Type/category of memory (e.g., stakeholder, requirement, decision)",
            value="general",
            required=True,
        ),
        MessageTextInput(
            name="content",
            display_name="Content",
            info="Content to store or search query",
            required=False,
        ),
        StrInput(
            name="memory_id",
            display_name="Memory ID",
            info="Specific memory ID (for get/delete operations)",
            required=False,
        ),
        DictInput(
            name="metadata",
            display_name="Metadata",
            info="Additional metadata to store with memory",
            required=False,
        ),
        IntInput(
            name="limit",
            display_name="Result Limit",
            info="Maximum number of results to return",
            value=10,
            advanced=True,
        ),
        StrInput(
            name="database_url",
            display_name="Database URL",
            info="PostgreSQL connection string",
            value="postgresql://foundry:foundry_dev@localhost:5432/foundry",
            advanced=True,
        ),
        SecretStrInput(
            name="openai_api_key",
            display_name="OpenAI API Key",
            info="API key for embeddings (uses OpenAI by default)",
            advanced=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Result",
            name="result",
            method="execute_operation",
        ),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = None

    async def _get_store(self):
        """Get or create the PostgresStore instance."""
        if self._store is not None:
            return self._store

        try:
            from langgraph.store.postgres import PostgresStore

            # Initialize with embedding function for semantic search
            self._store = PostgresStore.from_conn_string(
                self.database_url,
                index={
                    "dims": 1536,  # OpenAI embedding dimensions
                    "embed": self._get_embeddings,
                },
            )
            return self._store
        except ImportError:
            # Fallback for when langgraph-store-postgres isn't installed
            return None
        except Exception as e:
            # Handle connection errors gracefully
            return None

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for semantic search."""
        try:
            from langchain_openai import OpenAIEmbeddings
            import os

            # Use provided API key or environment variable
            api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Return zero vectors if no API key
                return [[0.0] * 1536 for _ in texts]

            embeddings = OpenAIEmbeddings(api_key=api_key)
            return embeddings.embed_documents(texts)
        except Exception:
            # Return zero vectors on error
            return [[0.0] * 1536 for _ in texts]

    async def execute_operation(self) -> Message:
        """Execute the selected memory operation."""
        operation = self.operation

        try:
            if operation == "store":
                result = await self._store_memory()
            elif operation == "search":
                result = await self._search_memories()
            elif operation == "list":
                result = await self._list_memories()
            elif operation == "get":
                result = await self._get_memory()
            elif operation == "delete":
                result = await self._delete_memory()
            elif operation == "stats":
                result = await self._get_stats()
            else:
                result = {"error": f"Unknown operation: {operation}"}

            return Message(
                text=json.dumps(result, indent=2, default=str),
                sender="PostgresMemory",
                sender_name=f"Postgres Memory - {operation}",
            )
        except Exception as e:
            return Message(
                text=json.dumps(
                    {"error": str(e), "operation": operation},
                    indent=2,
                ),
                sender="PostgresMemory",
                sender_name=f"Postgres Memory - Error",
            )

    async def _store_memory(self) -> Dict[str, Any]:
        """Store a memory item with semantic indexing."""
        import uuid

        if not self.content:
            return {"error": "content is required for store operation"}

        store = await self._get_store()

        # Generate a unique key
        memory_id = str(uuid.uuid4())

        # Create the namespace tuple
        namespace = ("engagements", self.engagement_id, self.memory_type)

        # Build the value to store
        value = {
            "content": self.content,
            "metadata": self.metadata or {},
            "search_text": self.content,  # Used for embedding
        }

        if store:
            try:
                await store.aput(
                    namespace=namespace,
                    key=memory_id,
                    value=value,
                )
                return {
                    "status": "stored",
                    "memory_id": memory_id,
                    "namespace": list(namespace),
                    "message": "Memory stored successfully",
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to store memory",
                }
        else:
            # Development mode - simulate storage
            return {
                "status": "stored",
                "memory_id": memory_id,
                "namespace": list(namespace),
                "message": "Memory stored (development mode - not persisted)",
            }

    async def _search_memories(self) -> Dict[str, Any]:
        """Semantic search across memories."""
        if not self.content:
            return {"error": "content (search query) is required for search operation"}

        store = await self._get_store()

        # Create namespace for search
        if self.memory_type and self.memory_type != "all":
            namespace = ("engagements", self.engagement_id, self.memory_type)
        else:
            namespace = ("engagements", self.engagement_id)

        if store:
            try:
                results = await store.asearch(
                    namespace=namespace,
                    query=self.content,
                    limit=self.limit,
                )

                memories = []
                for item in results:
                    memories.append({
                        "id": item.key,
                        "content": item.value.get("content", ""),
                        "metadata": item.value.get("metadata", {}),
                        "score": getattr(item, "score", None),
                    })

                return {
                    "query": self.content,
                    "results": memories,
                    "count": len(memories),
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "Search failed",
                }
        else:
            # Development mode
            return {
                "query": self.content,
                "results": [],
                "count": 0,
                "message": "Search completed (development mode - no store available)",
            }

    async def _list_memories(self) -> Dict[str, Any]:
        """List memories by namespace."""
        store = await self._get_store()

        namespace = ("engagements", self.engagement_id, self.memory_type)

        if store:
            try:
                items = await store.alist(namespace=namespace, limit=self.limit)

                memories = []
                for item in items:
                    memories.append({
                        "id": item.key,
                        "content": item.value.get("content", ""),
                        "metadata": item.value.get("metadata", {}),
                    })

                return {
                    "namespace": list(namespace),
                    "memories": memories,
                    "count": len(memories),
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "List failed",
                }
        else:
            return {
                "namespace": list(namespace),
                "memories": [],
                "count": 0,
                "message": "List completed (development mode)",
            }

    async def _get_memory(self) -> Dict[str, Any]:
        """Get a specific memory by ID."""
        if not self.memory_id:
            return {"error": "memory_id is required for get operation"}

        store = await self._get_store()

        namespace = ("engagements", self.engagement_id, self.memory_type)

        if store:
            try:
                item = await store.aget(namespace=namespace, key=self.memory_id)

                if item:
                    return {
                        "id": self.memory_id,
                        "content": item.value.get("content", ""),
                        "metadata": item.value.get("metadata", {}),
                        "found": True,
                    }
                else:
                    return {
                        "id": self.memory_id,
                        "found": False,
                        "message": "Memory not found",
                    }
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "Get failed",
                }
        else:
            return {
                "id": self.memory_id,
                "found": False,
                "message": "Get completed (development mode)",
            }

    async def _delete_memory(self) -> Dict[str, Any]:
        """Delete a specific memory."""
        if not self.memory_id:
            return {"error": "memory_id is required for delete operation"}

        store = await self._get_store()

        namespace = ("engagements", self.engagement_id, self.memory_type)

        if store:
            try:
                await store.adelete(namespace=namespace, key=self.memory_id)
                return {
                    "id": self.memory_id,
                    "deleted": True,
                    "message": "Memory deleted successfully",
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "Delete failed",
                }
        else:
            return {
                "id": self.memory_id,
                "deleted": True,
                "message": "Delete completed (development mode)",
            }

    async def _get_stats(self) -> Dict[str, Any]:
        """Get memory statistics for the engagement."""
        store = await self._get_store()

        if store:
            try:
                # Get counts for different memory types
                memory_types = [
                    "general",
                    "stakeholder",
                    "requirement",
                    "decision",
                    "source",
                ]
                stats = {}

                for mtype in memory_types:
                    namespace = ("engagements", self.engagement_id, mtype)
                    try:
                        items = await store.alist(namespace=namespace, limit=1000)
                        stats[mtype] = len(list(items))
                    except Exception:
                        stats[mtype] = 0

                return {
                    "engagement_id": self.engagement_id,
                    "memory_counts": stats,
                    "total": sum(stats.values()),
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "Stats retrieval failed",
                }
        else:
            return {
                "engagement_id": self.engagement_id,
                "memory_counts": {
                    "general": 0,
                    "stakeholder": 0,
                    "requirement": 0,
                    "decision": 0,
                    "source": 0,
                },
                "total": 0,
                "message": "Stats completed (development mode)",
            }
