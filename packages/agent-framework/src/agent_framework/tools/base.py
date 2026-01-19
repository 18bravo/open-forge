"""
Base tool classes for Open Forge agents.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool, ToolException
from core.observability.tracing import traced, get_tracer

tracer = get_tracer(__name__)


class ToolInput(BaseModel):
    """Base class for tool inputs."""
    pass


class ToolOutput(BaseModel):
    """Base class for tool outputs."""
    success: bool = True
    data: Any = None
    error: Optional[str] = None


class OpenForgeTool(BaseTool, ABC):
    """
    Base class for Open Forge agent tools.

    Provides:
    - Standardized input/output handling
    - Tracing integration
    - Error handling
    """

    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> ToolOutput:
        """Execute the tool logic. Override in subclasses."""
        pass

    @traced()
    async def _arun(self, **kwargs: Any) -> str:
        """Async run with tracing."""
        try:
            result = await self._execute(**kwargs)
            if result.success:
                return str(result.data)
            else:
                raise ToolException(result.error or "Tool execution failed")
        except Exception as e:
            raise ToolException(str(e))

    def _run(self, **kwargs: Any) -> str:
        """Sync run - raises error since we prefer async."""
        raise NotImplementedError("Use async execution with _arun")


class DatabaseQueryTool(OpenForgeTool):
    """Tool for querying the database."""

    name: str = "database_query"
    description: str = "Execute a read-only SQL query against the database"

    class InputSchema(BaseModel):
        query: str = Field(..., description="SQL query to execute")
        params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")

    args_schema: Type[BaseModel] = InputSchema

    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory

    async def _execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> ToolOutput:
        from sqlalchemy import text
        try:
            async with self.session_factory() as session:
                result = await session.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result.fetchall()]
                return ToolOutput(success=True, data=rows)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GraphQueryTool(OpenForgeTool):
    """Tool for querying the knowledge graph."""

    name: str = "graph_query"
    description: str = "Execute a Cypher query against the knowledge graph"

    class InputSchema(BaseModel):
        query: str = Field(..., description="Cypher query to execute")
        params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")

    args_schema: Type[BaseModel] = InputSchema

    def __init__(self, graph_db):
        super().__init__()
        self.graph_db = graph_db

    async def _execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> ToolOutput:
        try:
            from core.database.connection import get_async_db
            async with get_async_db() as session:
                results = await self.graph_db.execute_cypher(session, query, params)
                return ToolOutput(success=True, data=results)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class EventPublishTool(OpenForgeTool):
    """Tool for publishing events to the event bus."""

    name: str = "publish_event"
    description: str = "Publish an event to the message bus"

    class InputSchema(BaseModel):
        event_type: str = Field(..., description="Type of event to publish")
        payload: Dict[str, Any] = Field(..., description="Event payload")

    args_schema: Type[BaseModel] = InputSchema

    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus

    async def _execute(self, event_type: str, payload: Dict[str, Any]) -> ToolOutput:
        try:
            event_id = await self.event_bus.publish(event_type, payload)
            return ToolOutput(success=True, data={"event_id": event_id})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class DataLakeQueryTool(OpenForgeTool):
    """Tool for querying the Iceberg data lake."""

    name: str = "data_lake_query"
    description: str = "Query data from the Iceberg data lake"

    class InputSchema(BaseModel):
        namespace: str = Field(..., description="Iceberg namespace")
        table_name: str = Field(..., description="Table to query")
        filter_expr: Optional[str] = Field(default=None, description="Filter expression")
        columns: Optional[List[str]] = Field(default=None, description="Columns to select")
        limit: Optional[int] = Field(default=100, description="Maximum rows to return")

    args_schema: Type[BaseModel] = InputSchema

    def __init__(self, iceberg_catalog):
        super().__init__()
        self.catalog = iceberg_catalog

    async def _execute(
        self,
        namespace: str,
        table_name: str,
        filter_expr: Optional[str] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = 100
    ) -> ToolOutput:
        try:
            df = self.catalog.read_table(
                namespace=namespace,
                table_name=table_name,
                columns=columns,
                filter_expr=filter_expr,
                limit=limit
            )
            return ToolOutput(success=True, data=df.to_dicts())
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ToolRegistry:
    """Registry for managing available tools."""

    _tools: Dict[str, OpenForgeTool] = {}

    @classmethod
    def register(cls, tool: OpenForgeTool) -> None:
        """Register a tool."""
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> Optional[OpenForgeTool]:
        """Get a tool by name."""
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> List[str]:
        """List all registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def get_all(cls) -> List[OpenForgeTool]:
        """Get all registered tools."""
        return list(cls._tools.values())
