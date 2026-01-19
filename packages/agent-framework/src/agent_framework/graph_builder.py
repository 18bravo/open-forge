"""
LangGraph builder utilities for creating agent workflows.
"""
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from core.config import get_settings

settings = get_settings()

StateType = TypeVar("StateType", bound=BaseModel)

class AgentGraphBuilder:
    """Builder for creating LangGraph agent workflows."""
    
    def __init__(self, state_class: Type[StateType]):
        self.state_class = state_class
        self.workflow = StateGraph(state_class)
        self._nodes: Dict[str, Callable] = {}
        self._edges: List[tuple] = []
        self._conditional_edges: List[tuple] = []
        self._entry_point: Optional[str] = None
    
    def add_node(self, name: str, func: Callable) -> "AgentGraphBuilder":
        """Add a node to the graph."""
        self._nodes[name] = func
        self.workflow.add_node(name, func)
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> "AgentGraphBuilder":
        """Add a direct edge between nodes."""
        self._edges.append((from_node, to_node))
        self.workflow.add_edge(from_node, to_node)
        return self
    
    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable,
        path_map: Dict[str, str]
    ) -> "AgentGraphBuilder":
        """Add a conditional edge from a node."""
        self._conditional_edges.append((from_node, condition, path_map))
        self.workflow.add_conditional_edges(from_node, condition, path_map)
        return self
    
    def set_entry_point(self, node: str) -> "AgentGraphBuilder":
        """Set the entry point of the graph."""
        self._entry_point = node
        self.workflow.set_entry_point(node)
        return self
    
    def set_finish_point(self, node: str) -> "AgentGraphBuilder":
        """Set a node as a finish point."""
        self.workflow.add_edge(node, END)
        return self
    
    async def build(self, checkpointer: bool = True) -> Any:
        """Build and return the compiled graph."""
        if checkpointer:
            saver = await AsyncPostgresSaver.from_conn_string(
                settings.database.async_connection_string
            )
            await saver.setup()
            return self.workflow.compile(checkpointer=saver)
        return self.workflow.compile()
    
    def build_sync(self, checkpointer: bool = False) -> Any:
        """Build and return the compiled graph (sync version)."""
        return self.workflow.compile()


def create_subgraph(
    name: str,
    state_class: Type[StateType],
    nodes: Dict[str, Callable],
    edges: List[tuple],
    entry_point: str
) -> StateGraph:
    """Create a subgraph that can be used as a node."""
    builder = AgentGraphBuilder(state_class)
    
    for node_name, func in nodes.items():
        builder.add_node(node_name, func)
    
    for edge in edges:
        if len(edge) == 2:
            builder.add_edge(edge[0], edge[1])
        else:
            builder.add_conditional_edge(edge[0], edge[1], edge[2])
    
    builder.set_entry_point(entry_point)
    
    return builder.build_sync(checkpointer=False)