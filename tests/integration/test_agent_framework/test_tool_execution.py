"""
Integration tests for agent tool execution.

Tests tool registration, execution through agents, and tool output handling.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock
import json

from tests.integration.conftest import requires_postgres, requires_redis


pytestmark = pytest.mark.integration


class TestToolRegistry:
    """Tests for tool registry."""

    def test_register_tool(self):
        """Test registering a tool."""
        from agent_framework.tools.base import ToolRegistry, OpenForgeTool, ToolOutput
        from pydantic import BaseModel

        class TestToolInput(BaseModel):
            value: str

        class TestTool(OpenForgeTool):
            name = "test_tool"
            description = "A test tool"
            args_schema = TestToolInput

            async def _execute(self, value: str) -> ToolOutput:
                return ToolOutput(success=True, data=f"processed: {value}")

        tool = TestTool()
        ToolRegistry.register(tool)

        assert ToolRegistry.get("test_tool") is tool

    def test_list_tools(self):
        """Test listing registered tools."""
        from agent_framework.tools.base import ToolRegistry, OpenForgeTool, ToolOutput
        from pydantic import BaseModel

        class Tool1Input(BaseModel):
            x: int

        class Tool1(OpenForgeTool):
            name = "list_tool_1"
            description = "Tool 1"
            args_schema = Tool1Input

            async def _execute(self, x: int) -> ToolOutput:
                return ToolOutput(success=True, data=x)

        class Tool2(OpenForgeTool):
            name = "list_tool_2"
            description = "Tool 2"
            args_schema = Tool1Input

            async def _execute(self, x: int) -> ToolOutput:
                return ToolOutput(success=True, data=x)

        ToolRegistry.register(Tool1())
        ToolRegistry.register(Tool2())

        tool_names = ToolRegistry.list_tools()

        assert "list_tool_1" in tool_names
        assert "list_tool_2" in tool_names

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        from agent_framework.tools.base import ToolRegistry

        result = ToolRegistry.get("nonexistent_tool_xyz")
        assert result is None


class TestDatabaseQueryTool:
    """Tests for database query tool."""

    @pytest.mark.asyncio
    @requires_postgres
    async def test_database_query_execution(self, async_db_session):
        """Test executing a database query through the tool."""
        from agent_framework.tools.base import DatabaseQueryTool

        # Create a mock session factory
        async def session_factory():
            return async_db_session

        tool = DatabaseQueryTool(session_factory=session_factory)

        result = await tool._execute(query="SELECT 1 as value")

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["value"] == 1

    @pytest.mark.asyncio
    async def test_database_query_with_params(self):
        """Test database query with parameters."""
        from agent_framework.tools.base import DatabaseQueryTool, ToolOutput
        from sqlalchemy import text

        # Mock session
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(_mapping={"id": 1, "name": "test"})
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def session_factory():
            class MockContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, *args):
                    pass

            return MockContextManager()

        # Create the tool and execute the query
        tool = DatabaseQueryTool(session_factory=session_factory)

        result = await tool._execute(
            query="SELECT id, name FROM users WHERE id = :user_id",
            params={"user_id": 1}
        )

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["id"] == 1
        assert result.data[0]["name"] == "test"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_query_error_handling(self):
        """Test database query error handling."""
        from agent_framework.tools.base import DatabaseQueryTool

        # Mock session that raises an error
        async def failing_session_factory():
            class MockContextManager:
                async def __aenter__(self):
                    mock = MagicMock()
                    mock.execute = AsyncMock(side_effect=Exception("DB Error"))
                    return mock

                async def __aexit__(self, *args):
                    pass

            return MockContextManager()

        tool = DatabaseQueryTool(session_factory=failing_session_factory)

        result = await tool._execute(query="SELECT 1")

        assert result.success is False
        assert "DB Error" in result.error


class TestGraphQueryTool:
    """Tests for graph query tool."""

    @pytest.mark.asyncio
    async def test_graph_query_execution(self):
        """Test executing a graph query through the tool."""
        from agent_framework.tools.base import GraphQueryTool

        # Mock graph database
        mock_graph_db = MagicMock()
        mock_graph_db.execute_cypher = AsyncMock(return_value=[
            {"name": "Node1"},
            {"name": "Node2"}
        ])

        tool = GraphQueryTool(graph_db=mock_graph_db)

        # We need to mock get_async_db as well
        with pytest.MonkeyPatch.context() as m:
            mock_session = MagicMock()

            class MockContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, *args):
                    pass

            m.setattr(
                "agent_framework.tools.base.get_async_db",
                lambda: MockContextManager()
            )

            result = await tool._execute(
                query="MATCH (n) RETURN n.name as name",
                params={}
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_graph_query_with_params(self):
        """Test graph query with parameters."""
        from agent_framework.tools.base import GraphQueryTool

        mock_graph_db = MagicMock()
        mock_graph_db.execute_cypher = AsyncMock(return_value=[
            {"id": "123", "type": "Person"}
        ])

        tool = GraphQueryTool(graph_db=mock_graph_db)

        # Verify tool accepts params
        assert tool.name == "graph_query"
        assert "Cypher" in tool.description


class TestEventPublishTool:
    """Tests for event publishing tool."""

    @pytest.mark.asyncio
    async def test_event_publish_execution(self):
        """Test publishing an event through the tool."""
        from agent_framework.tools.base import EventPublishTool

        mock_event_bus = MagicMock()
        mock_event_bus.publish = AsyncMock(return_value="msg-123")

        tool = EventPublishTool(event_bus=mock_event_bus)

        result = await tool._execute(
            event_type="test.event",
            payload={"data": "test_value"}
        )

        assert result.success is True
        assert result.data["event_id"] == "msg-123"
        mock_event_bus.publish.assert_called_once_with(
            "test.event",
            {"data": "test_value"}
        )

    @pytest.mark.asyncio
    async def test_event_publish_error_handling(self):
        """Test event publish error handling."""
        from agent_framework.tools.base import EventPublishTool

        mock_event_bus = MagicMock()
        mock_event_bus.publish = AsyncMock(side_effect=Exception("Publish failed"))

        tool = EventPublishTool(event_bus=mock_event_bus)

        result = await tool._execute(
            event_type="test.event",
            payload={"data": "test"}
        )

        assert result.success is False
        assert "Publish failed" in result.error


class TestDataLakeQueryTool:
    """Tests for data lake query tool."""

    @pytest.mark.asyncio
    async def test_data_lake_query(self):
        """Test querying the data lake."""
        from agent_framework.tools.base import DataLakeQueryTool
        import polars as pl

        mock_catalog = MagicMock()
        mock_df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["a", "b", "c"]
        })
        mock_catalog.read_table = MagicMock(return_value=mock_df)

        tool = DataLakeQueryTool(iceberg_catalog=mock_catalog)

        result = await tool._execute(
            namespace="test_ns",
            table_name="test_table",
            columns=["id", "name"],
            limit=10
        )

        assert result.success is True
        assert len(result.data) == 3

    @pytest.mark.asyncio
    async def test_data_lake_query_with_filter(self):
        """Test data lake query with filter expression."""
        from agent_framework.tools.base import DataLakeQueryTool
        import polars as pl

        mock_catalog = MagicMock()
        mock_df = pl.DataFrame({
            "id": [1],
            "status": ["active"]
        })
        mock_catalog.read_table = MagicMock(return_value=mock_df)

        tool = DataLakeQueryTool(iceberg_catalog=mock_catalog)

        result = await tool._execute(
            namespace="test_ns",
            table_name="test_table",
            filter_expr="status = 'active'",
            limit=100
        )

        assert result.success is True


class TestToolExecutionInAgent:
    """Tests for tool execution within an agent workflow."""

    @pytest.mark.asyncio
    async def test_agent_with_tools(self, mock_llm):
        """Test agent that uses tools."""
        from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
        from agent_framework.state_management import AgentState
        from agent_framework.tools.base import OpenForgeTool, ToolOutput
        from contracts.agent_interface import AgentInput
        from langgraph.graph import StateGraph, END
        from pydantic import BaseModel

        class CalculateInput(BaseModel):
            a: int
            b: int

        class CalculateTool(OpenForgeTool):
            name = "calculate"
            description = "Add two numbers"
            args_schema = CalculateInput

            async def _execute(self, a: int, b: int) -> ToolOutput:
                return ToolOutput(success=True, data=a + b)

        class ToolUsingAgent(BaseOpenForgeAgent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.calculate_tool = CalculateTool()

            @property
            def name(self) -> str:
                return "tool_using_agent"

            @property
            def description(self) -> str:
                return "Agent that uses tools"

            @property
            def required_inputs(self) -> List[str]:
                return ["numbers"]

            @property
            def output_keys(self) -> List[str]:
                return ["sum"]

            def get_system_prompt(self) -> str:
                return "You are an agent."

            def get_tools(self) -> List[Any]:
                return [self.calculate_tool]

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def use_tool(state: AgentState) -> Dict[str, Any]:
                    context = state.get("agent_context", {})
                    numbers = context.get("numbers", [0, 0])

                    result = await self.calculate_tool._execute(
                        a=numbers[0],
                        b=numbers[1]
                    )

                    return {
                        "outputs": {"sum": result.data},
                        "current_step": "done"
                    }

                graph.add_node("use_tool", use_tool)
                graph.set_entry_point("use_tool")
                graph.add_edge("use_tool", END)

                return graph

        agent = ToolUsingAgent(llm=mock_llm)

        input_data = AgentInput(
            engagement_id="test-eng",
            phase="test",
            context={"numbers": [5, 3]}
        )

        output = await agent.run(input_data)

        assert output.success is True
        assert output.outputs["sum"] == 8

    @pytest.mark.asyncio
    async def test_agent_tool_error_handling(self, mock_llm):
        """Test agent handling tool errors."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState
        from agent_framework.tools.base import OpenForgeTool, ToolOutput
        from contracts.agent_interface import AgentInput
        from langgraph.graph import StateGraph, END
        from pydantic import BaseModel

        class FailingInput(BaseModel):
            trigger: str

        class FailingTool(OpenForgeTool):
            name = "failing_tool"
            description = "A tool that fails"
            args_schema = FailingInput

            async def _execute(self, trigger: str) -> ToolOutput:
                if trigger == "fail":
                    return ToolOutput(success=False, error="Tool failed intentionally")
                return ToolOutput(success=True, data="ok")

        class ToolErrorAgent(BaseOpenForgeAgent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.failing_tool = FailingTool()

            @property
            def name(self) -> str:
                return "tool_error_agent"

            @property
            def description(self) -> str:
                return "Agent testing tool errors"

            @property
            def required_inputs(self) -> List[str]:
                return []

            @property
            def output_keys(self) -> List[str]:
                return ["status"]

            def get_system_prompt(self) -> str:
                return "You are an agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    result = await self.failing_tool._execute(trigger="fail")

                    if not result.success:
                        return {
                            "outputs": {"status": "tool_failed", "error": result.error},
                            "errors": [result.error],
                            "current_step": "error"
                        }

                    return {
                        "outputs": {"status": "ok"},
                        "current_step": "done"
                    }

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = ToolErrorAgent(llm=mock_llm)

        input_data = AgentInput(
            engagement_id="test-eng",
            phase="test",
            context={}
        )

        output = await agent.run(input_data)

        assert output.outputs.get("status") == "tool_failed"


class TestToolOutputFormatting:
    """Tests for tool output formatting."""

    @pytest.mark.asyncio
    async def test_tool_output_serialization(self):
        """Test that tool outputs serialize correctly."""
        from agent_framework.tools.base import ToolOutput

        output = ToolOutput(
            success=True,
            data={
                "items": [1, 2, 3],
                "metadata": {"count": 3}
            }
        )

        # Should be serializable to string
        str_output = str(output.data)
        assert "items" in str_output

    @pytest.mark.asyncio
    async def test_tool_output_with_complex_data(self):
        """Test tool output with complex nested data."""
        from agent_framework.tools.base import ToolOutput

        complex_data = {
            "level1": {
                "level2": {
                    "level3": ["a", "b", "c"]
                }
            },
            "array": [
                {"id": 1, "value": "x"},
                {"id": 2, "value": "y"}
            ]
        }

        output = ToolOutput(success=True, data=complex_data)

        assert output.data["level1"]["level2"]["level3"] == ["a", "b", "c"]
        assert output.data["array"][0]["id"] == 1
